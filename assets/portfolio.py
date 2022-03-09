# Класс портфеля, используемого для хранения активов и оценки прибыльности
# той или иной стратегии
import json
import os
import typing as tp
from datetime import date, timedelta

import numpy as np
import pandas as pd

from storage import CloudManager, DatabaseManager


class Portfolio:
    def __init__(self, filename: tp.Optional[str] = None):
        self.shares_table = pd.DataFrame({
            'ticker': pd.Series([], dtype=str),
            'number': pd.Series([], dtype=np.int),
            'open_price': pd.Series([], dtype=np.float),
            'close_price': pd.Series([], dtype=np.float),
            'open_date': pd.Series([], dtype='datetime64[ns]'),
            'close_date': pd.Series([], dtype='datetime64[ns]'),
            'is_closed': pd.Series([], dtype=np.bool)
        })
        self.history = {}
        self.initial_funds = 100000.0
        self.free_funds = 100000.0
        self.cloud_manager = CloudManager()
        self.database_manager = DatabaseManager()
        if filename is not None:
            self.load(filename)

    def buy(self, share_ticker: str, number: int,
            price: tp.Optional[float] = None,
            purchase_date: date = date.today()) -> bool:
        """
        Покупка акций по указанной цене
        """
        # если цена не указана, берём текущую рыночную цену из базы
        if price is None:
            price = self.database_manager.get_share_info(share_ticker)['price']

        cost = number * price
        if cost > self.free_funds:
            print('Недостаточно средств для покупки')
            return False

        row = {'ticker': share_ticker, 'number': number, 'open_price': price,
               'closed_price': None, 'open_date': purchase_date,
               'closed_date': None, 'is_closed': False}
        self.shares_table = self.shares_table.append(row, ignore_index=True)

        self.free_funds -= cost
        return True

    def sell(self, share_ticker: str, number: int,
             price: tp.Optional[float] = None,
             sale_date: date = date.today()) -> bool:
        """
        Продажа акций по указанной цене
        """
        # если цена не указана, берём текущую рыночную цену из базы
        if price is None:
            price = self.database_manager.get_share_info(share_ticker)['price']

        shares = self.shares_table[self.shares_table['ticker'] == share_ticker]
        others1 = shares[shares['is_closed']]
        shares = shares[~shares['is_closed']]

        # проверяем, есть ли в портфеле такое количество акций
        shares_number = shares['number'].sum()
        if shares_number < number:
            print("В портфеле недостаточно акций. В нём {} акций {}".format(
                shares_number, share_ticker))
            return False

        shares = shares.sort_values(by=['open_date']).reset_index(drop=True)
        shares_cumsum = shares['number'].cumsum()
        sold_shares = (shares_cumsum <= number)

        # если необходимо, делим одну из ячеек на две (проданные и нет)
        sold_len = sold_shares.sum()
        if sold_len > 0:
            lower_bound = shares_cumsum[sold_shares].iloc[-1]
        else:
            lower_bound = 0

        if lower_bound < number:
            new_row = shares.loc[sold_len].copy()
            new_row['number'] = number - lower_bound
            shares = shares.append(new_row, ignore_index=True)

            shares.loc[sold_len, 'number'] -= new_row['number']
            sold_shares = sold_shares.append(pd.Series([True]),
                                             ignore_index=True)

        shares.loc[sold_shares, 'closed_price'] = price
        shares.loc[sold_shares, 'closed_date'] = sale_date
        shares.loc[sold_shares, 'is_closed'] = True

        others2 = self.shares_table[self.shares_table['ticker'] != share_ticker]
        self.shares_table = pd.concat([others1, others2, shares])
        self.shares_table.index = np.arange(len(self.shares_table))
        self.free_funds += number * price
        return True

    def _save_table(self, table: pd.DataFrame, filename: str) -> None:
        """
        Сохранение табличных данных в csv-файл
        """
        table.to_csv(filename)
        self.cloud_manager.upload_to_cloud(filename)
        os.remove(filename)

    def save(self, filename: str) -> None:
        """
        Сохранение прортфеля в файл
        """
        base, ext = os.path.splitext(filename)
        shares_filename = base + '_shares.csv'
        data = {
            'initial_funds': self.initial_funds,
            'free_funds': self.free_funds,
            'shares_table': shares_filename,
            'history': self.history
        }
        with open(filename, 'w', encoding='utf-8') as json_file:
            json.dump(data, json_file)
        self.cloud_manager.upload_to_cloud(filename)
        os.remove(filename)

        self._save_table(self.shares_table, shares_filename)

    def _load_table(self, filename: str) -> pd.DataFrame:
        """
        Загрузка табличных данных из csv-файла
        """
        self.cloud_manager.download_from_cloud(filename)
        table = pd.read_csv(filename, index_col=0)
        os.remove(filename)
        return table

    def load(self, filename: str) -> None:
        """
        Загрузка прортфеля из файла
        """
        self.cloud_manager.download_from_cloud(filename)
        with open(filename, 'r', encoding='utf-8') as json_file:
            data = json.load(json_file)
        os.remove(filename)

        self.initial_funds = data['initial_funds']
        self.free_funds = data['free_funds']
        self.history = data['history']
        self.shares_table = self._load_table(data['shares_table'])

    def get_all_funds(self) -> float:
        """
        Получение текущей стоимости портфеля
        """
        all_funds = self.free_funds
        shares = self.shares_table[~self.shares_table['is_closed']]

        # считаем текущую стоимомть всех акций в портфеле
        for i, share in shares.iterrows():
            ticker = share['ticker']
            num = share['number']
            term = self.database_manager.get_share_info(ticker)['price'] * num
            all_funds += term

        return all_funds

    def get_total_profitability(self) -> float:
        """
        Получение текущей прибыльности портфеля
        """
        all_funds = self.get_all_funds()
        return all_funds / self.initial_funds - 1.0

    def get_range_profitability(self, first: date,
                                last: date = date.today()) -> float:
        """
        Получение прибыльности портфеля в заданном диапазоне
        (границы включительно)
        """
        while str(first) not in self.history.keys():
            first += timedelta(1)
        while str(last) not in self.history.keys():
            last -= timedelta(1)
        return self.history[str(last)] / self.history[str(first)] - 1.0

    def get_shares_dict(self) -> dict:
        """
        Получение тикеров всех акций, находящихся в портфеле, вместе
        с их количеством
        """
        shares = self.shares_table[~self.shares_table['is_closed']]
        return shares.groupby(by='ticker')['number'].sum().to_dict()

    def update_history(self) -> None:
        """
        Сохранение истории стоимости портфеля
        """
        self.history[str(date.today())] = self.get_all_funds()

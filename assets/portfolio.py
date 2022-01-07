import json
import os
from datetime import date

import numpy as np
import pandas as pd

from storage import CloudManager, DatabaseManager


class Portfolio:
    def __init__(self, filename=None):
        self.shares_table = pd.DataFrame({
            'ticker': pd.Series([], dtype=str),
            'open_price': pd.Series([], dtype=np.float),
            'close_price': pd.Series([], dtype=np.float),
            'open_date': pd.Series([], dtype='datetime64[ns]'),
            'close_date': pd.Series([], dtype='datetime64[ns]'),
            'is_closed': pd.Series([], dtype=np.bool)
        })
        self.history = {}
        self.initial_funds = 100000.0
        self.free_funds = 100000.0
        if filename is not None:
            self.load(filename)
        self.cloud_manager = CloudManager()
        self.database_manager = DatabaseManager()

    def buy(self, share_ticker, number, price, purchase_date=date.today()):
        cost = number * price
        if cost > self.free_funds:
            print('Недостаточно средств для покупки')
            return False

        row = {'ticker': share_ticker, 'open_price': price,
               'closed_price': None, 'open_date': purchase_date,
               'closed_date': None, 'is_closed': False}
        for i in range(number):
            self.shares_table.append(row)

        self.free_funds -= cost
        return True

    def sell(self, share_ticker, number, price, sale_date=date.today()):
        shares = self.shares_table[self.shares_table['ticker'] == share_ticker]

        shares_number = shares.shape[0]
        if shares_number < number:
            print("В портфеле недостаточно акций. В нём {} акций {}".format(
                number, share_ticker))
            return False

        shares = shares.sort_values(by=['open_date'])
        shares.loc[:number - 1, 'closed_price'] = price
        shares.loc[:number - 1, 'closed_date'] = sale_date
        shares.loc[:number - 1, 'is_closed'] = True
        others = self.shares_table[self.shares_table['ticker'] != share_ticker]
        self.shares_table = pd.concat([others, shares])
        self.free_funds += number * price
        return True

    def _save_table(self, table, filename):
        table.to(filename)
        self.cloud_manager.upload_to_cloud(filename)
        os.remove(filename)

    def save(self, filename):
        base, ext = os.path.splitext(filename)
        shares_filename = base + '_shares.csv'
        data = {
            'initial_funds': self.initial_funds,
            'free_funds': self.free_funds,
            'shares_table': shares_filename,
            'history': self.history
        }
        with open(filename, 'wb') as json_file:
            json.dump(data, json_file)
        self.cloud_manager.upload_to_cloud(filename)
        os.remove(filename)

        self._save_table(self.shares_table, shares_filename)

    def _load_table(self, filename):
        self.cloud_manager.download_from_cloud(filename)
        table = pd.read_csv(filename)
        os.remove(filename)
        return table

    def load(self, filename):
        self.cloud_manager.download_from_cloud(filename)
        with open(filename, 'rb') as json_file:
            data = json.load(json_file)
        os.remove(filename)

        self.initial_funds = data['initial_funds']
        self.free_funds = data['free_funds']
        self.history = data['history']
        self.shares_table = self._load_table(data['shares_table'])

    def get_all_funds(self):
        all_funds = self.free_funds
        for i, share in self.shares_table.iterrows():
            ticker = share['ticker']
            all_funds += self.database_manager.get_share_info(ticker)

        # сохраняем историю стоимости портфеля
        self.history[date.today()] = all_funds

        return all_funds

    def get_profitability(self):
        all_funds = self.get_all_funds()
        return all_funds / self.initial_funds - 1.0

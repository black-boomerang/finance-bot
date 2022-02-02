# Класс, отвечающий за анализ показателей компаний и формирование рейтинга акций

import os
import time
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

from assets import Portfolio
from storage import CloudManager, DatabaseManager


class Analyzer:
    def __init__(self):
        self.database_manager = DatabaseManager()
        self.cloud_manager = CloudManager()
        self.portfolio = Portfolio()

        self.yahoo_columns = ['Rating', 'Low Target', 'Current Price',
                              'Average Target', 'High Target']

        # получение последней таблицы с данными
        last_date = datetime.today()
        filename = self._get_ranking_filename(last_date)
        while not self.cloud_manager.download_from_cloud(filename):
            last_date -= timedelta(1)
            filename = self._get_ranking_filename(last_date)
        self.last_ranking = pd.read_csv(filename, index_col=0)
        os.remove(filename)

    @staticmethod
    def _get_ranking_filename(date):
        return 'ordered_ranks_' + date.strftime('%Y_%m_%d') + '.csv'

    @staticmethod
    def _get_ranks_dict(order_filter, table_type, param):
        """
        Формирование рейтинга компаний по финансовому показателю (order_filter).
        Последовательный "просмотр" страниц сайта finviz.com при помощи BeautifulSoup
        """
        start_url = 'https://finviz.com/screener.ashx?v=1' + str(
            table_type) + '1&o={}&r='.format(order_filter)
        ranks = dict()
        params = dict()

        print('Загрузка показателей c finviz:')
        for i in tqdm(range(1, 8389, 20)):
            url = start_url + str(i)
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; '
                                     'Win64; x64) AppleWebKit/537.36 '
                                     '(KHTML, like Gecko) '
                                     'Chrome/92.0.4515.131 '
                                     'Safari/537.36 OPR/78.0.4093.147'}

            for attempt in range(4):
                page = requests.get(url, headers=headers)
                soup = BeautifulSoup(page.text, 'lxml')
                try:
                    tbl = soup.find('table', bgcolor='#d3d3d3')
                    rows = tbl.findAll('tr', valign='top')
                    for row in rows:
                        tds = row.findAll('td')
                        ranks[tds[1].text] = int(tds[0].text)
                        string_value = tds[param].text.strip('%')
                        if string_value == '-':
                            string_value = 'NaN'
                        params[tds[1].text] = float(string_value)
                    break
                except:
                    if attempt == 3:
                        print(f'Ошибка на стороне finviz: {page.text}')
                    else:
                        time.sleep((attempt + 1) * 15)

        return ranks, params

    def _get_new_ranking(self):
        """
        Формирование рейтинга компаний по финансовым показателям P/E и ROE
        """
        white_list = pd.read_excel(
            os.path.join('resources', 'white_list.xlsx'))
        tickers = white_list['Торговый код'].to_list()

        pe_ranks, pe = self._get_ranks_dict('pe', 1, 7)
        roe_ranks, roe = self._get_ranks_dict('-roe', 6, 5)

        ep_rang_series = pd.Series(pe_ranks, name='E/P rang')
        ep_series = (100 / pd.Series(pe, name='E/P (%)'))
        roe_rang_series = pd.Series(roe_ranks, name='ROE rang')
        roe_series = pd.Series(roe, name='ROE (%)')

        series = [ep_rang_series, ep_series, roe_rang_series, roe_series]
        ranks = pd.concat(series, axis=1, sort=False)
        ranks['Summary rang'] = ranks['E/P rang'] + ranks['ROE rang']

        need_tickers_ranks = ranks.loc[ranks.index.intersection(tickers)]
        idx = np.unique(need_tickers_ranks.index, return_index=True)[1]
        need_tickers_ranks = need_tickers_ranks.iloc[idx]
        last_ranking = self.last_ranking.drop(self.yahoo_columns, axis=1)
        need_tickers_ranks = need_tickers_ranks.combine_first(last_ranking)
        return need_tickers_ranks.sort_values('Summary rang')

    @staticmethod
    def _get_quote_estimation(ticker):
        """
        Получение текущей цены и прогнозов на цену акции, а также значения "привлекательности"
        этой акции для покупки по версии yahoo
        """
        ticker = ticker.replace('@', '.')
        url = r'https://query1.finance.yahoo.com/v10/finance/quoteSummary/{0}?modules=financialData'.format(
            ticker)
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; '
                                 'Win64; x64) AppleWebKit/537.36 '
                                 '(KHTML, like Gecko) '
                                 'Chrome/92.0.4515.131 '
                                 'Safari/537.36 OPR/78.0.4093.147'}

        response = requests.get(url, headers=headers)
        data = response.json()['quoteSummary']['result'][0]['financialData']
        rating = data['recommendationMean']['raw']
        low = data['targetLowPrice']['raw']
        current = data['currentPrice']['raw']
        average = data['targetMeanPrice']['raw']
        high = data['targetHighPrice']['raw']

        return [rating, low, current, average, high]

    def _get_estimation(self, tickers):
        """
        Получение текущих цен и прогнозов на цены акций для заданных тикеров
        """
        estimation = pd.DataFrame(index=tickers, columns=self.yahoo_columns)
        print('Загрузка данных с yahoo:')
        for ticker in tqdm(tickers):
            for i in range(5):
                try:
                    estimation.loc[ticker] = self._get_quote_estimation(ticker)
                    break
                except Exception:
                    pass
        return estimation

    def _save_info_to_database(self, ranking):
        """
        Сохранение информации об акциях в базу
        """
        print('Загрузка данных в базу:')
        for ticker, row in tqdm(ranking.iterrows()):
            self.database_manager \
                .insert_update_share_info(ticker, row['E/P (%)'],
                                          row['ROE (%)'], row['Current Price'],
                                          row['Rating'], row['Low Target'],
                                          row['Average Target'],
                                          row['High Target'])

    def _get_ranking(self):
        """
        Формирование рейтинга компаний по финансовым показателям P/E и ROE
        и сохранение его в базу
        """
        recent_date = datetime.today()
        weekday = recent_date.weekday()
        recent_date -= timedelta((weekday > 4) + (weekday > 5))
        filename = self._get_ranking_filename(recent_date)

        # формирование таблицы происходит только по будням
        if datetime.today().weekday() <= 4:
            # ранжирование акций по показателям P/E и ROE
            ranking = self._get_new_ranking()
            tickers = ranking.index.to_list()

            # получение прогнозов на акции по версии аналитиков
            estimation = self._get_estimation(tickers)
            ranking = pd.concat([ranking, estimation], axis=1)
            ranking.to_csv(filename)

            # сохранение информации в базу
            self._save_info_to_database(ranking)

            # загрузка таблицы в облако
            self.cloud_manager.upload_to_cloud(filename)
        else:
            self.cloud_manager.download_from_cloud(filename)
            ranking = pd.read_csv(filename, index_col=0)
        os.remove(filename)

        return ranking

    @staticmethod
    def _selection_function(ranking, companies_number=5):
        """
        Функция отбора недооценённых акций
        """
        return ranking[
            ranking['Current Price'] < ranking['Average Target']].head(
            companies_number * 6).dropna().sort_values(
            'Rating').head(companies_number)

    def update_portfolio(self, best_companies):
        """
        Обновление портфеля с учётом изменений в рейтинге акций
        """
        # продажа акций, покинувших топ рейтинга
        tickers_count = 0
        for ticker, number in self.portfolio.get_shares_dict().items():
            if ticker not in best_companies.index.tolist():
                self.portfolio.sell(ticker, number)
                tickers_count += 1

        # покупка акций, только что попавших в топ рейтинга
        money_per_ticker = self.portfolio.free_funds / max(tickers_count, 1)
        for ticker in best_companies.index.tolist():
            if ticker not in self.portfolio.get_shares_dict().keys():
                price = self.database_manager.get_share_info(ticker)['price']
                number = money_per_ticker // price

                # остаток денег перераспределяем между остальными компаниями
                tickers_count -= 1
                if tickers_count > 0:
                    rest = money_per_ticker - price * number
                    money_per_ticker += rest / tickers_count

                self.portfolio.buy(ticker, number, price)

        # обновляем историю стоимости портфеля и сохраняем его в хранилище
        self.portfolio.update_history()
        self.portfolio.save('portfolio_v1.json')

    def get_best_companies(self, companies_number=5):
        """
        Определение лучших для покупки акций по версии анализатора.
        Возвращает два значения: первое - лучшие companies_number акций,
        второе - изменился ли их список по сравнению с предыдущим
        """
        ranking = self._get_ranking()

        cur_best = self._selection_function(ranking, companies_number)
        prev_best = self._selection_function(self.last_ranking,
                                             companies_number)
        self.last_ranking = ranking

        # обновление портфеля
        self.update_portfolio(cur_best)

        is_changed = (set(prev_best.index) == set(cur_best.index))
        return cur_best, is_changed

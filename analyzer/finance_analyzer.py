# Класс, отвечающий за анализ показателей компаний и формирование рейтинга акций

import os
import time
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup

from storage import CloudManager


class Analyzer:
    def __init__(self):
        self.cloud_manager = CloudManager()
        self.yahoo_columns = ['Rating', 'Low Target', 'Current Price',
                              'Average Target', 'High Target']

    @staticmethod
    def _get_ranking_filename(date):
        return 'ordered_ranks_' + date.strftime('%Y_%m_%d') + '.csv'

    @staticmethod
    def _get_ranks_dict(order_filter, table_type, param):
        '''
        Формирование рейтинга компаний по финансовому показателю (order_filter).
        Последовательный "просмотр" страниц сайта finviz.com при помощи BeautifulSoup
        '''
        start_url = 'https://finviz.com/screener.ashx?v=161' + str(
            table_type) + '1&o={}&r='.format(order_filter)
        ranks = dict()
        params = dict()

        for i in range(1, 8389, 20):
            if i % 400 == 1:
                print(i * 100 // 8389, '%')

            url = start_url + str(i)
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; '
                                     'Win64; x64) AppleWebKit/537.36 '
                                     '(KHTML, like Gecko) '
                                     'Chrome/92.0.4515.131 '
                                     'Safari/537.36 OPR/78.0.4093.147'}

            for attempt in range(3):
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
                    if attempt == 2:
                        print(f'Ошибка на стороне finviz: {page.text}')
                    else:
                        time.sleep(60)

        return ranks, params

    def _get_new_ranking(self, old_ranking=None):
        '''
        Формирование рейтинга компаний по финансовым показателям P/E и ROE
        '''
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
        need_tickers_ranks = need_tickers_ranks.combine_first(old_ranking)
        return need_tickers_ranks.sort_values('Summary rang')

    @staticmethod
    def _get_quote_estimation(ticker):
        '''
        Получение текущей цены и прогнозов на цену акции, а также значения "привлекательности"
        этой акции для покупки по версии yahoo
        '''
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
        '''
        Получение текущих цен и прогнозов на цены акций для заданных тикеров
        '''
        estimation = pd.DataFrame(index=tickers, columns=self.yahoo_columns)
        for ticker in tickers:
            for i in range(5):
                try:
                    estimation.loc[ticker] = self._get_quote_estimation(ticker)
                    print(ticker + ' is analyzed')
                    break
                except Exception:
                    pass
        return estimation

    def _get_candidates(self, companies_number=30):
        '''
        Отбор самых недооценённых акций, рекомендованных для покупки
        '''
        recent_date = datetime.today()
        weekday = recent_date.weekday()
        recent_date -= timedelta((weekday > 4) + (weekday > 5))
        filename = self._get_ranking_filename(recent_date)

        # формирование таблицы происходит только по будням
        if datetime.today().weekday() <= 4:
            # получение предыдущей таблицы для обработки
            # ошибок при формировании новой
            previous_date = recent_date - timedelta(1)
            weekday = previous_date.weekday()
            previous_date -= timedelta((weekday > 4) + (weekday > 5))
            old_filename = self._get_ranking_filename(previous_date)
            self.cloud_manager.download_from_cloud(old_filename)
            old_ranking = pd.read_csv(old_filename, index_col=0)
            old_ranking = old_ranking.drop(self.yahoo_columns, axis=1)
            os.remove(old_filename)

            # ранжирование акций по показателям P/E и ROE
            ranking = self._get_new_ranking(old_ranking)
            primaries_number = companies_number * 4
            primary_companies = ranking.head(primaries_number).index.to_list()

            # получение прогнозов на акции по версии аналитиков
            estimation = self._get_estimation(primary_companies)
            ranking = pd.concat([ranking, estimation], axis=1)
            ranking.to_csv(filename)

            # загрузка таблицы в облако
            self.cloud_manager.upload_to_cloud(filename)
        else:
            self.cloud_manager.download_from_cloud(filename)
            ranking = pd.read_csv(filename, index_col=0)
        os.remove(filename)

        return ranking[
            ranking['Current Price'] < ranking['Average Target']].head(
            companies_number)

    def get_best_companies(self, companies_number=5):
        '''
        Определение лучших для покупки акций по версии анализатор
        '''
        candidates = self._get_candidates(companies_number * 6)
        return candidates.dropna().sort_values('Rating').head(companies_number)

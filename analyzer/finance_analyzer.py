import os
import re
from datetime import datetime, timedelta

import pandas as pd
from bs4 import BeautifulSoup
from requests_html import HTMLSession

from analyzer.cloud_manager import CloudManager


class Analyzer:
    def __init__(self):
        self.cloud_manager = CloudManager()

    @staticmethod
    def _get_ranking_filename(date):
        return 'ordered_ranks_' + date.strftime('%Y_%m_%d') + '.csv'

    @staticmethod
    def _get_ranks_dict(order_filter, table_type, param):
        start_url = 'https://finviz.com/screener.ashx?v=1' + str(
            table_type) + '1ft=3&o={}&r='.format(order_filter)
        ranks = dict()
        params = dict()

        for i in range(1, 7531, 20):
            if i % 400 == 1:
                print(i * 100 // 7531, '%')

            url = start_url + str(i)
            with HTMLSession() as session:
                page = session.get(url)

            soup = BeautifulSoup(page.text, 'lxml')
            tbl = soup.find('table', bgcolor='#d3d3d3')
            rows = tbl.findAll('tr', valign='top')
            for row in rows:
                tds = row.findAll('td')
                ranks[tds[1].text] = int(tds[0].text)
                params[tds[1].text] = float(tds[param].text.strip('%') + '0')

        return ranks, params

    def _get_new_ranking(self):
        white_list = pd.read_excel(
            os.path.join('resources', 'white_list.xlsx'))
        tickers = white_list['Торговый код'].to_list()

        pe_ranks, pe = self._get_ranks_dict('pe', 1, 7)
        roe_ranks, roe = self._get_ranks_dict('-roe', 6, 5)

        ep_rang_series = pd.Series(pe_ranks, name='E/P rang')
        ep_series = (1 / pd.Series(pe, name='E/P (%)')) * 100
        roe_rang_series = pd.Series(roe_ranks, name='ROE rang')
        roe_series = pd.Series(roe, name='ROE (%)')

        series = [ep_rang_series, ep_series, roe_rang_series, roe_series]
        ranks = pd.concat(series, axis=1, sort=False)
        ranks['Summary rang'] = ranks['E/P rang'] + ranks['ROE rang']

        need_tickers_ranks = ranks.loc[ranks.index.intersection(tickers)]
        return need_tickers_ranks.sort_values('Summary rang')

    @staticmethod
    def _get_quote_estimation(ticker, timeout=60):

        url = 'https://finance.yahoo.com/quote/{0}/analysis?p={0}'.format(
            ticker)
        with HTMLSession() as session:
            page = session.get(url)

        for i in range(5):
            try:
                page.html.render(wait=4, sleep=4, timeout=timeout,
                                 scrolldown=4)
                text = page.html.html
                rating = [re.search(
                    r'\d*\.?\d+ on a scale of 1 to 5, where 1 is Strong Buy and 5 is Sell',
                    text).group(0).split()[0]]
                values = re.search(
                    r'Low  \d*\.?\d+ Current  \d*\.?\d+ Average  \d*\.?\d+ High  \d*\.?\d+',
                    text).group(0).split()[1::2]
                break
            except Exception:
                print('EstimationError!')

        return list(map(float, rating + values))

    def _get_estimation(self, tickers):
        columns = ['Rating', 'Low Target', 'Current Price', 'Average Target',
                   'High Target']
        estimation = pd.DataFrame(index=tickers, columns=columns)
        for ticker in tickers:
            estimation.loc[ticker] = self._get_quote_estimation(ticker)
            print(ticker + ' is analyzed')
        return estimation

    def _get_candidates(self, companies_number=30):
        recent_date = datetime.today()
        weekday = recent_date.weekday()
        recent_date -= timedelta((weekday > 4) + (weekday > 5))
        filename = self._get_ranking_filename(recent_date)

        if datetime.today().weekday() <= 4:
            ranking = self._get_new_ranking()
            primary_companies = ranking.head(companies_number).index.to_list()
            estimation = self._get_estimation(primary_companies)
            ranking = pd.concat([ranking, estimation], axis=1)
            ranking.to_csv(filename)
            self.cloud_manager.upload_to_cloud(filename)
        else:
            self.cloud_manager.download_from_cloud(filename)
            ranking = pd.read_csv(filename, index_col=0)
        os.remove(filename)

        return ranking.head(companies_number)

    def get_best_companies(self, companies_number=5):
        candidates = self._get_candidates(companies_number * 6)
        return candidates.dropna().sort_values('Rating').head(companies_number)

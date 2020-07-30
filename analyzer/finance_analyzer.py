import os
import re
from datetime import datetime, timedelta

import pandas as pd
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

import settings
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
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; '
                                     'Win64; x64) AppleWebKit/537.36 '
                                     '(KHTML, like Gecko) '
                                     'Chrome/83.0.4103.116 '
                                     'Safari/537.36 OPR/69.0.3686.95'}
            page = requests.get(url, headers=headers)

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

    def _get_quote_estimation(self, ticker, timeout=60):
        url = 'https://finance.yahoo.com/quote/{0}/analysis?p={0}'.format(
            ticker)

        self.driver.get(url)
        self.driver.execute_script(
            "document.getElementById('Col2-4-QuoteModule-Proxy').scrollIntoView();")
        rating = [self.driver.find_element_by_xpath(
            r'//*[@data-test="rec-rating-txt"]').text]
        self.driver.execute_script(
            "document.getElementById('Col2-5-QuoteModule-Proxy').scrollIntoView();")
        text = self.driver.find_element_by_xpath(
            r'//*[@class="Mb(35px) smartphone_Px(20px)"]').get_attribute(
            'outerHTML')
        values = re.search(
            r'Low  \d*\.?\d+ Current  \d*\.?\d+ Average  \d*\.?\d+ High  \d*\.?\d+',
            text).group(0).split()[1::2]

        return list(map(float, rating + values))

    @staticmethod
    def _chrome_init():
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920x1080')
        chrome_options.add_argument('start-maximised')
        chrome_options.binary_location = settings.GOOGLE_CHROME_BIN

        driver = webdriver.Chrome(
            executable_path=settings.CHROMEDRIVER_PATH,
            chrome_options=chrome_options)
        driver.implicitly_wait(60)
        return driver

    def _get_estimation(self, tickers):
        columns = ['Rating', 'Low Target', 'Current Price', 'Average Target',
                   'High Target']
        estimation = pd.DataFrame(index=tickers, columns=columns)
        self.driver = self._chrome_init()
        for ticker in tickers:
            for i in range(5):
                try:
                    estimation.loc[ticker] = self._get_quote_estimation(ticker)
                    print(ticker + ' is analyzed')
                    break
                except Exception:
                    pass
        self.driver.quit()
        return estimation

    def _get_candidates(self, companies_number=30):
        recent_date = datetime.today()
        weekday = recent_date.weekday()
        recent_date -= timedelta((weekday > 4) + (weekday > 5))
        filename = self._get_ranking_filename(recent_date)

        if datetime.today().weekday() <= 4:
            ranking = self._get_new_ranking()
            primaries_number = companies_number * 4
            primary_companies = ranking.head(primaries_number).index.to_list()
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

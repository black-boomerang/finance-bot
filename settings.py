# Загрузка необходимых ID и токенов

import os

CLOUDCUBE_ACCESS_KEY_ID = os.getenv('CLOUDCUBE_ACCESS_KEY_ID')
CLOUDCUBE_SECRET_ACCESS_KEY = os.getenv('CLOUDCUBE_SECRET_ACCESS_KEY')
TELEGRAM_API_TOKEN = os.getenv('TELEGRAM_API_TOKEN')
CLOUDCUBE_URL = os.getenv('CLOUDCUBE_URL')
DATABASE_URL = os.getenv('DATABASE_URL_QL')
CHROMEDRIVER_PATH = os.getenv('CHROMEDRIVER_PATH')
GOOGLE_CHROME_BIN = os.getenv('GOOGLE_CHROME_BIN')

PROFIT_TAX = 0.13
MONTH_NAMES = ('январь', 'февраль', 'март', 'апрель', 'май', 'июнь', 'июль',
               'август', 'сентябрь', 'октябрь', 'ноябрь', 'декабрь')

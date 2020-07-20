import matplotlib.pyplot as plt
import pandas as pd
import yfinance as yf


def save_history(ticker):
    stock = yf.Ticker(ticker)
    hist = stock.history(period='max')
    hist.to_csv(ticker + '_history.csv')


def ticker_info(ticker):
    stock = yf.Ticker(ticker)
    print(stock.info)


def analyze(ticker):
    file_name = ticker + '_history.csv'
    ticker_info = pd.read_csv(file_name, index_col='Date')
    ticker_info['Weekday'] = pd.to_datetime(ticker_info.index).weekday
    ticker_info.hist(by='Weekday')
    ticker_info['Volume'].plot()
    plt.legend()
    plt.show()


ticker_info('ge')

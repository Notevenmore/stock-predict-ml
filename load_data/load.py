import yfinance as yf
import pandas as pd

from load_data.embed_data import embed_data
from load_data.load_orderbook import load_orderbook
from config import config

class Load:
    def __init__(self):
        self.news = embed_data
        self.orderbook = load_orderbook
        self.ihsg = None
        self.stock = {}
        self.data = {}

        self.update_saved_data()
        self.load_ohlcv()
        self.load_ihsg()
        self.load_data()

    def load_data(self):
        for stock in config.stocks:
            self.merged_data(stock)
        
        print(self.data)

    def merged_data(self, stock_name):
        if self.news.processed_news[stock_name] is not None or self.orderbook.orderbook[stock_name] is not None or self.ihsg is not None or self.stock[stock_name] is not None:
            self.news.processed_news[stock_name]['date'] = pd.to_datetime(self.news.processed_news[stock_name]['date']).astype(config.astype_date_data)
            self.stock[stock_name]['date'] = pd.to_datetime(self.stock[stock_name]['date']).astype(config.astype_date_data)
            self.ihsg['date'] = pd.to_datetime(self.ihsg['date']).astype(config.astype_date_data)
            self.ihsg['Close_ihsg'] = self.ihsg['Close']
            self.orderbook.orderbook[stock_name]['date'] = pd.to_datetime(self.orderbook.orderbook[stock_name]['date']).astype(config.astype_date_data)

            self.data[stock_name] = pd.merge(self.stock[stock_name], self.news.processed_news[stock_name], on='date', how='left', validate="one_to_one")
            self.data[stock_name] = pd.merge(self.data[stock_name], self.ihsg[['date', 'Close_ihsg']], on='date', how='left', validate="one_to_one")
            self.data[stock_name] = pd.merge(self.data[stock_name], self.orderbook.orderbook[stock_name][['date', 'value', 'offer_value', 'offer_volume', 'bid_value', 'bid_volume', 'foreign_sell', 'foreign_buy']], on='date', how='left', validate="one_to_one")
            self.data[stock_name].select_dtypes('number').fillna(0, inplace=True)
        else:
            self.data[stock_name] = None

    def update_saved_data(self):
        self.save_ohlcv()
        self.load_ohlcv()

        self.save_ihsg()
        self.load_ihsg()

        self.news.save_embedded_data()
        self.news.load_embedded_data()

        self.orderbook.update_orderbook_data()
        self.orderbook.load_orderbook_data()

    def save_ohlcv(self):
        for stock in config.stocks:
            df = yf.download(stock+'.JK', start=config.start, end=config.end)
            df.columns = df.columns.droplevel(1)
            df.columns.name = None
            df = df.reset_index()
            df.to_csv(f"data/Technical/{stock}.csv")

    def save_ihsg(self):
        df_ihsg = yf.download('^JKSE', start=config.start, end=config.end)
        df_ihsg.columns = df_ihsg.columns.droplevel(1)
        df_ihsg.columns.name = None
        df_ihsg = df_ihsg.reset_index()
        df_ihsg.to_csv("data/IHSG.csv")

    def load_ohlcv(self):
        for stock in config.stocks:
            try:
                self.stock[stock] = pd.read_csv(f'data/Technical/{stock}.csv')
                self.stock[stock].drop(columns=['Unnamed: 0'], inplace=True)
                self.stock[stock].rename(columns={'Date': 'date'}, inplace=True)
            except FileNotFoundError:
                self.stock[stock] = None

    def load_ihsg(self):
        try:
            self.ihsg = pd.read_csv('data/IHSG.csv')
            self.ihsg.drop(columns=['Unnamed: 0'], inplace=True)
            self.ihsg.rename(columns={'Date': 'date'}, inplace=True)
        except FileNotFoundError:
            self.ihsg = None
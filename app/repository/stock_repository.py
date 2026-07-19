import yfinance as yf
import pandas as pd
from config import config
from database import StockDB
from flask import current_app as app

class StockRepository:
    def __init__(self, is_init = False):
        self.ihsg = None
        self.stock = {}

        if is_init:
            self.load_ohlcv()
            self.load_ihsg()

    def get_stocks(self):
        with app.app_context():
            stocks = StockDB.query.all()

        return stocks

    def save_ohlcv(self):
        with app.app_context():
            stocks = [
                stock.code for stock in StockDB.query.all()
            ]

        for stock in stocks:
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
        with app.app_context():
            stocks = [
                stock.code for stock in StockDB.query.all()
            ]

        for stock in stocks:
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
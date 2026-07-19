from repository import StockRepository, ProcessedDataRepository, OrderbookRepository
from config import config
from flask import current_app as app
from database import StockDB
import pandas as pd

class StockModel:
    def __init__(self):
        self.repository = StockRepository()
        self.orderbook_repository = None
        self.processed_data_repository = None
            
        self.data = None

    def get_stocks(self):
        return self.repository.get_stocks()
    
    def get_stock_data(self, stock_name):
        if self.data is None:
            return []
        
        if self.data[stock_name] is None:
            return []
        
        return self.data[stock_name]

    def processed_all_data(self):
        self.orderbook_repository = OrderbookRepository(is_init=True)
        self.processed_data_repository = ProcessedDataRepository(is_init=True)

        self.repository.load_ihsg()
        self.repository.load_ohlcv()
        
        self.orderbook_repository.load_orderbook_data()
        self.processed_data_repository.load_embedded_data()

        if self.processed_data_repository.processed_news is not None and self.orderbook_repository.orderbook is not None :
            stock_list = self.repository.get_stocks()
            with app.app_context():
                stocks = [
                    stock.code for stock in stock_list
                ]

            if len(stocks) > 0:
                self.data = {}
                
                for stock in stocks:
                    self.__load_data(stock)

    def __load_data(self, stock_name):
        if self.processed_data_repository.processed_news.get(stock_name) is not None and self.orderbook_repository.orderbook.get(stock_name) is not None and self.repository.ihsg is not None and self.repository.stock.get(stock_name) is not None:
            self.processed_data_repository.processed_news[stock_name]['date'] = pd.to_datetime(self.processed_data_repository.processed_news[stock_name]['date'], format="mixed").astype(config.astype_date_data)
            self.repository.stock[stock_name]['date'] = pd.to_datetime(self.repository.stock[stock_name]['date'], format="mixed").astype(config.astype_date_data)
            self.repository.ihsg['date'] = pd.to_datetime(self.repository.ihsg['date'], format="mixed").astype(config.astype_date_data)
            self.repository.ihsg['Close_ihsg'] = self.repository.ihsg['Close']
            self.orderbook_repository.orderbook[stock_name]['date'] = pd.to_datetime(self.orderbook_repository.orderbook[stock_name]['date'], format="mixed").astype(config.astype_date_data)

            self.data[stock_name] = pd.merge(self.repository.stock[stock_name], self.processed_data_repository.processed_news[stock_name], on='date', how='inner', validate="one_to_one")
            self.data[stock_name] = pd.merge(self.data[stock_name], self.repository.ihsg[['date', 'Close_ihsg']], on='date', how='inner', validate="one_to_one")
            self.data[stock_name] = pd.merge(self.data[stock_name], self.orderbook_repository.orderbook[stock_name][['date', 'value', 'offer_value', 'offer_volume', 'bid_value', 'bid_volume', 'foreign_sell', 'foreign_buy']], on='date', how='inner', validate="one_to_one")
            
            numeric_cols = self.data[stock_name].select_dtypes('number').columns
            self.data[stock_name][numeric_cols] = self.data[stock_name][numeric_cols].fillna(0)
        else:
            self.data[stock_name] = None

    def load_routine_stock(self):
        self.repository.save_ohlcv()
        self.repository.load_ohlcv()

        self.repository.save_ihsg()
        self.repository.load_ihsg()
from repository import StockRepository, ProcessedDataRepository, OrderbookRepository
from config import config

import pandas as pd

class StockModel:
    def __init__(self):
        self.repository = StockRepository()
        self.orderbook_repository = OrderbookRepository()
        self.processed_data_repository = ProcessedDataRepository()
        self.data = None

        self.__processed_all_data()

    def get_stocks(self):
        return config.stocks
    
    def get_stock_data(self, stock_name):
        if self.data is None:
            return []
        
        if self.data[stock_name] is None:
            return []
        
        return self.data[stock_name]

    def __processed_all_data(self):
        if self.processed_data_repository.processed_news is not None and self.orderbook_repository.orderbook is not None :
            if len(config.stocks) > 0:
                self.data = {}
            for stock in config.stocks:
                self.__load_data(stock)

    def __load_data(self, stock_name):
        if self.processed_data_repository.processed_news[stock_name] is not None and self.orderbook_repository.orderbook[stock_name] is not None and self.repository.ihsg is not None and self.repository.stock[stock_name] is not None:
            self.processed_data_repository.processed_news[stock_name]['date'] = pd.to_datetime(self.processed_data_repository.processed_news[stock_name]['date'], format="mixed").astype(config.astype_date_data)
            self.repository.stock[stock_name]['date'] = pd.to_datetime(self.repository.stock[stock_name]['date'], format="mixed").astype(config.astype_date_data)
            self.repository.ihsg['date'] = pd.to_datetime(self.repository.ihsg['date'], format="mixed").astype(config.astype_date_data)
            self.repository.ihsg['Close_ihsg'] = self.repository.ihsg['Close']
            self.orderbook_repository.orderbook[stock_name]['date'] = pd.to_datetime(self.orderbook_repository.orderbook[stock_name]['date'], format="mixed").astype(config.astype_date_data)

            print("MERGE REPOSITORY STOCK PROCESSED NEWS")
            self.data[stock_name] = pd.merge(self.repository.stock[stock_name], self.processed_data_repository.processed_news[stock_name], on='date', how='inner', validate="one_to_one")
            print("MERGE REPOSITORY STOCK IHSG")
            self.data[stock_name] = pd.merge(self.data[stock_name], self.repository.ihsg[['date', 'Close_ihsg']], on='date', how='inner', validate="one_to_one")
            print("MERGE REPOSITORY STOCK ORDERBOOK")
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
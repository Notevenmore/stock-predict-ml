from datetime import datetime
from database import StockDB
import re
import os
import json
from dotenv import load_dotenv
import torch

load_dotenv()
class Config:
    REGEX_WORD_BOUNDARY = r'\b(?:{pattern})\b'

    def __init__(self):
        self.db_username = os.getenv("DB_USERNAME")
        self.db_password = os.getenv("DB_PASSWORD")
        self.db_name = os.getenv("DB_NAME")
        self.db_port = os.getenv("DB_PORT")
        self.db_host = os.getenv("DB_HOST")

        self.SQLALCHEMY_DATABASE_URI = (
            f"postgresql://{self.db_username}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )
        self.SQLALCHEMY_TRACK_MODIFICATIONS = False
        
        self.stocks = []
        self.stock_categories = {}

        self.start = os.getenv("START")
        self.end = datetime.now().strftime("%Y-%m-%d")
        
        self.orderbook_url = os.getenv("ORDERBOOK_URL")
        
        self.media_keywords = json.loads(os.getenv("MEDIA_KEYWORDS"))
        self.news_national_keys = set(json.loads(os.getenv("KEYWORD_NATIONAL")))
        self.news_international_keys = set(json.loads(os.getenv("KEYWORD_INTERNATIONAL")))
        self.company_international_keys = {}

        self.news_national_key_lower = [news_national_key.lower() for news_national_key in self.news_national_keys]
        self.news_international_key_lower = [news_international_key.lower() for news_international_key in self.news_international_keys]
        self.company_international_key_lower = {}

        self.national_pattern = self.build_pattern(self.news_national_key_lower)
        self.international_pattern = self.build_pattern(self.news_international_key_lower)
        self.company_pattern = {}

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.astype_date_data = 'datetime64[s]'
    
    def load_stock(self):
        stocks = StockDB.query.all()
        self.stock_categories = {stock.code: stock.categories for stock in stocks}
        self.stocks = [
            stock.code for stock in stocks
        ]

        self.company_international_keys = {
            stock: {stock} | set(self.stock_categories[stock])
            for stock in self.stocks
        }

        self.company_international_key_lower = {
            stock: [
                company_international_key.lower() for company_international_key in self.company_international_keys[stock]
            ]
            for stock in self.stocks
        }

        self.company_pattern = {
            stock: self.build_pattern(self.company_international_key_lower[stock]) 
            for stock in self.stocks
        }

    @staticmethod
    def build_pattern(keywords):
        sorted_keys = sorted(keywords, key=len, reverse=True)
        pattern = '|'.join(map(re.escape, sorted_keys))

        return re.compile(
            Config.REGEX_WORD_BOUNDARY.format(pattern=pattern),
            re.IGNORECASE
        )
    
    @staticmethod
    def get_end():
        return datetime.now().strftime("%Y-%m-%d")
    

config = Config()
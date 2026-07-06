from datetime import datetime
import re
import os
import json
from dotenv import load_dotenv
import torch

load_dotenv()
class Config:
    REGEX_WORD_BOUNDARY = r'\b(?:{pattern})\b'

    def __init__(self):
        self.stocks = ['BNBR', 'BUMI', 'PADI']
        self.stock_categories = {
            "BNBR": ['Perdagangan', 'Konstruksi', 'Pertanian', 'Pertambangan', 'ENRG', 'BLD', 'BWPT', 'BTEL', 'BUMI', 'VKTR'],
            "BUMI": ['Pertambangan', 'Mineral', 'Energy', 'Energi', 'Sumber Daya Alam', 'SDA', 'migas', 'gas', 'Minyak'],
            "PADI": ['Keuangan']
        }
        self.media_keywords = json.loads(os.getenv("MEDIA_KEYWORDS"))
        self.start = os.getenv("START")
        self.end = datetime.now().strftime("%Y-%m-%d")
        self.orderbook_url = os.getenv("ORDERBOOK_URL")
        self.news_national_keys = set(json.loads(os.getenv("KEYWORD_NATIONAL")))
        self.news_international_keys = set(json.loads(os.getenv("KEYWORD_INTERNATIONAL")))
        self.company_international_keys = {
            stock: {stock} | set(self.stock_categories[stock])
            for stock in self.stocks
        }

        self.news_national_key_lower = [news_national_key.lower() for news_national_key in self.news_national_keys]
        self.news_international_key_lower = [news_international_key.lower() for news_international_key in self.news_international_keys]
        self.company_international_key_lower = {
            stock: [
                company_international_key.lower() for company_international_key in self.company_international_keys[stock]
            ]
            for stock in self.stocks
        }

        self.national_pattern = self.build_pattern(self.news_national_key_lower)
        self.international_pattern = self.build_pattern(self.news_international_key_lower)
        self.company_pattern = {
            stock: self.build_pattern(self.company_international_key_lower[stock]) 
            for stock in self.stocks
        }

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.astype_date_data = 'datetime64[s]'

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
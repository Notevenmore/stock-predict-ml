from repository import NewsRepository

class NewsModel:
    def __init__(self):
        self.repository = NewsRepository()
    
    def get_news(self, stock_name, page, limit):
        data = self.repository.get_news(stock_name, page, limit)
        if data is None:
            return []
        
        return data
    
    def load_routine_news(self):
        self.repository.update_news_data()
        self.repository.load_news_data()
    
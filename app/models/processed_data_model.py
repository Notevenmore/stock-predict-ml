from repository import ProcessedDataRepository

class ProcessedDataModel:
    def __init__(self):
        self.repository = ProcessedDataRepository()
    
    def get_processed_data(self, stock_name):
        data = self.repository.get_processed_news_data(stock_name)
        if data is None:
            return []
        
        return data
    
    def load_routine_processed_data(self):
        self.repository.save_embedded_data()
        self.repository.load_embedded_data()
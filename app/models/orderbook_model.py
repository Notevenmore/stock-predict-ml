from repository import OrderbookRepository

class OrderbookModel:
    def __init__(self):
        self.repository = OrderbookRepository()
    
    def get_orderbooks(self, stock_name):
        data = self.repository.get_orderbook(stock_name)
        if data is None:
            return []
        
        return data
    
    def load_routine_orderbook_data(self):
        self.repository.update_orderbook_data()
        self.repository.load_orderbook_data()
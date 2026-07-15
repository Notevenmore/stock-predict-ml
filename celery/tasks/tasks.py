from config import api_client

class Tasks:
    def update_news(self):
        return api_client.put("/news")

    def update_orderbook(self):
        return api_client.put("/orderbook")

    def update_processed_data(self):
        return api_client.put("/processed-data")

    def update_stock(self):
        return api_client.put("/stock")
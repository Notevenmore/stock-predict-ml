from flask import jsonify
from config import response
from models import NewsModel

class NewsController:
    def __init__(self):
        self.model = NewsModel()

    def get_list_news(self, stock_name):
        data = self.model.get_news(stock_name)
        return jsonify(response.success_response(
            message="Berhasil mendapatkan data berita saham",
            data=data
        ))
    
    def update_all_news_stock_data(self):
        try:
            self.model.load_routine_news()
            return jsonify(response.success_response(
                message="Berhasil update seluruh berita saham", 
                data=[]
            ))
        except Exception as e:
            return jsonify(response.error_response(
                code=500,
                message=f"Gagal update seluruh berita saham: {e}",
            ))
from flask import jsonify
from config import response
from server import Service
from models import NewsModel
import traceback

class NewsController:
    def __init__(self):
        self.model = NewsModel()
        self.service = Service()

    def get_list_news(self, stock_name, page, limit):
        data = self.model.get_news(stock_name, page, limit)
        return jsonify(response.success_response(
            message="Berhasil mendapatkan data berita saham",
            data=data
        ))
    
    def update_all_news_stock_data(self):
        try:
            self.model.load_routine_news()
            
            self.service.emit_events(
                "news_updated", 
                {
                    "status": "SUCCESS",
                    "code": 200,
                    "message": "Berhasil update seluruh berita saham",
                }  
            )

            return jsonify(response.success_response(
                message="Berhasil update seluruh berita saham", 
                data=[]
            ))
        except Exception as e:
            traceback.print_exc()
            
            return jsonify(response.error_response(
                code=500,
                message=f"Gagal update seluruh berita saham: {e}",
            ))
from flask import jsonify
from config import response
from server import Service
from models import OrderbookModel
import traceback

class OrderbookController:
    def __init__(self):
        self.model = OrderbookModel()
        self.service = Service()

    def get_list_orderbook(self, stock_name):
        data = self.model.get_orderbooks(stock_name)
        
        return jsonify(response.success_response(
            message="Berhasil mendapatkan data orderbook saham",
            data=data
        ))
    
    def update_all_orderbook_data(self):
        try:
            self.model.load_routine_orderbook_data()

            self.service.emit_events(
                "orderbook_updated",
                {
                    "status": "SUCCESS",
                    "code": 200,
                    "message": "Berhasil update seluruh data orderbook saham",
                }  
            )

            return jsonify(response.success_response(
                message="Berhasil update seluruh data orderbook saham", 
                data=[]
            ))
        except Exception as e:
            traceback.print_exc()
            
            return jsonify(response.error_response(
                code=500,
                message=f"Gagal update seluruh data orderbook saham: {e}",
            ))
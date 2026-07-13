from flask import jsonify
from config import response
from models import OrderbookModel

class OrderbookController:
    def __init__(self):
        self.model = OrderbookModel()

    def get_list_orderbook(self, stock_name):
        data = self.model.get_orderbooks(stock_name)
        
        return jsonify(response.success_response(
            message="Berhasil mendapatkan data orderbook saham",
            data=data
        ))
    
    def update_all_orderbook_data(self):
        try:
            self.model.load_routine_orderbook_data()
            return jsonify(response.success_response(
                message="Berhasil update seluruh data orderbook saham", 
                data=[]
            ))
        except Exception as e:
            return jsonify(response.error_response(
                code=500,
                message=f"Gagal update seluruh data orderbook saham: {e}",
            ))
from flask import jsonify
from config import response
from models import StockModel

class StockController:
    def __init__(self):
        self.model = StockModel()

    def get_stock(self):
        data = self.model.get_stocks()
        return jsonify(response.success_response(
            message="Berhasil mendapatkan data daftar saham", 
            data=data
        ))
    
    def get_stock_data(self, stock_name):
        data = self.model.get_stock_data(stock_name)
        return jsonify(response.success_response(
            message=f"Berhasil mendapatkan data saham {stock_name}", 
            data=data
        ))
    
    def update_all_stock_data(self):
        try:
            self.model.load_routine_stock()
            return jsonify(response.success_response(
                message="Berhasil update seluruh data saham", 
                data=[]
            ))
        except Exception as e:
            return jsonify(response.error_response(
                code=500,
                message=f"Gagal update seluruh data saham: {e}",
            ))
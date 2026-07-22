from flask import jsonify
from config import response
from server import Service
from models import StockModel
import traceback

class StockController:
    def __init__(self):
        self.model = StockModel()
        self.service = Service()

    def get_stock(self, page, limit):
        try:
            data = self.model.get_stocks(page, limit)
            return jsonify(response.success_response(
                message="Berhasil mendapatkan data daftar saham", 
                data=data
            ))
        except Exception as e:
            return jsonify(response.error_response(
                message=f"Gagal mendapatkan data daftar saham: {e}. Traceback: {traceback.print_exc()}"
            ))
    
    def get_stock_data(self, stock_name, range_days):
        try:
            data = self.model.get_stock_data(stock_name, range_days)
            return jsonify(response.success_response(
                message=f"Berhasil mendapatkan data saham {stock_name}", 
                data=data
            ))
        except Exception as e:
            return jsonify(response.error_response(
                message=f"Gagal mendapatkan data saham {stock_name}: {e}. Traceback: {traceback.print_exc()}"
            ))
    
    def get_all_stock_data(self, stock_name):
        try:
            result = self.model.get_all_stock_data(stock_name)
            return jsonify(response.success_response(
                message=f"Berhasil mendapatkan data saham {stock_name}", 
                data=result
            ))
        except Exception as e:
            return jsonify(response.error_response(
                message=f"Gagal mendapatkan data saham {stock_name}: {e}. Traceback: {traceback.print_exc()}"
            ))
    
    def update_all_stock_data(self):
        try:
            self.model.load_routine_stock()

            self.service.emit_events(
                "stock_updated",
                {
                    "status": "SUCCESS",
                    "code": 200,
                    "message": "Berhasil update seluruh data saham",
                }  
            )

            return jsonify(response.success_response(
                message="Berhasil update seluruh data saham", 
                data=[]
            ))
        except Exception as e:
            return jsonify(response.error_response(
                code=500,
                message=f"Gagal update seluruh data saham: {e} -> {traceback.print_exc()}",
            ))
from flask import jsonify
from config import response
from models import ProcessedDataModel

class ProcessedDataController:
    def __init__(self):
        self.model = ProcessedDataModel()

    def get_processed_data(self, stock_name):
        data = self.model.get_processed_data(stock_name)
        return jsonify(response.success_response(
            message="Berhasil mendapatkan data",
            data=data
        ))
    
    def update_all_processed_data(self):
        self.model.load_routine_processed_data()
        return jsonify(response.success_response(
            message="Berhasil memproses ulang data", 
            data=[]
        ))
        # try:
        # except Exception as e:
        #     return jsonify(response.error_response(
        #         code=500,
        #         message=f"Gagal memproses ulang data: {e}",
        #     ))

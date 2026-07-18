from flask import jsonify
from config import response
from server import Service
from models import ProcessedDataModel
import traceback

class ProcessedDataController:
    def __init__(self):
        self.model = ProcessedDataModel()
        self.service = Service()

    def get_processed_data(self, stock_name):
        data = self.model.get_processed_data(stock_name)
        return jsonify(response.success_response(
            message="Berhasil mendapatkan data",
            data=data
        ))
    
    def update_all_processed_data(self):
        try:
            self.model.load_routine_processed_data()

            self.service.emit_events(
                "process_data_updated",
                {
                    "status": "SUCCESS",
                    "code": 200,
                    "message": "Berhasil memproses ulang data",
                }  
            )

            return jsonify(response.success_response(
                message="Berhasil memproses ulang data", 
                data=[]
            ))
        except Exception as e:
            traceback.print_exc()
            
            return jsonify(response.error_response(
                code=500,
                message=f"Gagal memproses ulang data: {e}",
            ))

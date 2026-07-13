from flask import Blueprint
from controllers import ProcessedDataController

processed_data_bp = Blueprint('processed-data', __name__, url_prefix='/processed-data')
processed_data_controller = ProcessedDataController()

@processed_data_bp.route("", methods=["PUT"])
def update_processed_data():
    return processed_data_controller.update_all_processed_data()

@processed_data_bp.route("/<stock_name>", methods=["GET"])
def get_processed_data(stock_name):
    return processed_data_controller.get_processed_data(stock_name)
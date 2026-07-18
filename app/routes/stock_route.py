from flask import Blueprint
from controllers import StockController

stock_bp = Blueprint('stock', __name__, url_prefix='/stock')
stock_controller = StockController()

def initialize():
    stock_controller.model.repository.load_ohlcv()
    stock_controller.model.repository.load_ihsg()

@stock_bp.route("", methods=["PUT"])
def update_stocks():
    return stock_controller.update_all_stock_data()

@stock_bp.route("", methods=['GET'])
def get_list_stock():
    return stock_controller.get_stock()
from flask import Blueprint
from controllers import StockController

stock_bp = Blueprint('stock', __name__, url_prefix='/stock')
stock_controller = StockController()

@stock_bp.route("", methods=['GET'])
def get_list_stock():
    return stock_controller.get_stock()
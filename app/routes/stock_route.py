from flask import Blueprint, request
from controllers import StockController

stock_bp = Blueprint('stock', __name__, url_prefix='/stock')
stock_controller = StockController()

def initialize():
    stock_controller.model.repository.load_ohlcv()
    stock_controller.model.repository.load_ihsg()
    stock_controller.model.processed_all_data()

@stock_bp.route("", methods=["PUT"])
def update_stocks():
    return stock_controller.update_all_stock_data()

# Public Route
@stock_bp.route("", methods=['GET'])
def get_list_stock():
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 50))

    return stock_controller.get_stock(page, limit)

@stock_bp.route("/<stock_name>", methods=['GET'])
def get_stock_data(stock_name):
    range_days = int(request.args.get("range", 1))

    return stock_controller.get_stock_data(stock_name, range_days)

# ML Server Route Only

# Admin Server Route Only
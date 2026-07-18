from flask import Blueprint
from controllers import OrderbookController

orderbook_bp = Blueprint('orderbook', __name__, url_prefix='/orderbook')
orderbook_controller = OrderbookController()

def initialize():
    orderbook_controller.model.repository.load_orderbook_data()

@orderbook_bp.route("", methods=["PUT"])
def update_orderbook():
    return orderbook_controller.update_all_orderbook_data()

@orderbook_bp.route("/<stock_name>", methods=["GET"])
def get_list_orderbook(stock_name):
    return orderbook_controller.get_list_orderbook(stock_name)
    
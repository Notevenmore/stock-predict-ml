from flask import Blueprint
from controllers import OrderbookController

orderbook_bp = Blueprint('orderbook', __name__, url_prefix='/orderbook')
orderbook_controller = OrderbookController()

@orderbook_bp.route("/<stock_name>", methods=["GET"])
def get_list_orderbook(stock_name):
    return orderbook_controller.get_list_orderbook(stock_name)
    
from flask import Blueprint, request
from controllers import NewsController

news_bp = Blueprint('news', __name__, url_prefix='/news')
news_controller = NewsController()

def initialize():
    news_controller.model.repository.load_news_data()

@news_bp.route("/", methods=["PUT"])
def update_news():
    return news_controller.update_all_news_stock_data()

@news_bp.route("/<stock_name>", methods=["GET"])
def get_list_news(stock_name):
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 50))

    return news_controller.get_list_news(stock_name, page, limit)

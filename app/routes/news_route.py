from flask import Blueprint
from controllers import NewsController

news_bp = Blueprint('news', __name__, url_prefix='/news')
news_controller = NewsController()

@news_bp.route("/<stock_name>", methods=["GET"])
def get_list_news(stock_name):
    return news_controller.get_list_news(stock_name)
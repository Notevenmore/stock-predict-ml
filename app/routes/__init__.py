from .stock_route import stock_bp, initialize as init_stock
from .news_route import news_bp, initialize as init_news
from .orderbook_route import orderbook_bp, initialize as init_orderbook
from .processed_data_route import processed_data_bp, initialize as init_process_data

def register_blueprints(app):
    app.register_blueprint(stock_bp)
    app.register_blueprint(news_bp)
    app.register_blueprint(orderbook_bp)
    app.register_blueprint(processed_data_bp)

def initialize():
    init_news()
    init_orderbook()
    init_process_data()
    init_stock()
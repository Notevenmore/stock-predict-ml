from .stock_route import stock_bp
from .news_route import news_bp
from .orderbook_route import orderbook_bp
from .processed_data_route import processed_data_bp

def register_blueprints(app):
    app.register_blueprint(stock_bp)
    app.register_blueprint(news_bp)
    app.register_blueprint(orderbook_bp)
    app.register_blueprint(processed_data_bp)
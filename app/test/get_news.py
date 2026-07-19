from controllers import NewsController
from config import config
from flask import Flask
from database import StockDB

app = Flask(__name__)

with app.app_context():
    news_controller = NewsController()

    stocks = [
        stock.code for stock in StockDB.query.all()
    ]

    responses = {}
    for stock in config.stocks:
        responses[stock] = news_controller.get_list_news(stock)
        if hasattr(responses[stock], 'json'):
            responses[stock] = responses[stock].json
        elif hasattr(responses[stock], 'data'):
            responses[stock] = responses[stock].data

print(responses)


from controllers import NewsController
from config import config
from flask import Flask

app = Flask(__name__)

with app.app_context():
    news_controller = NewsController()
    responses = {}
    for stock in config.stocks:
        responses[stock] = news_controller.get_list_news(stock)
        if hasattr(responses[stock], 'json'):
            responses[stock] = responses[stock].json
        elif hasattr(responses[stock], 'data'):
            responses[stock] = responses[stock].data

print(responses)


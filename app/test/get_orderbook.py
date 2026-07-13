from controllers import OrderbookController
from config import config
from flask import Flask

app = Flask(__name__)

with app.app_context():
    orderbook_controller = OrderbookController()
    responses = {}
    for stock in config.stocks:
        responses[stock] = orderbook_controller.get_list_orderbook(stock)
        if hasattr(responses[stock], 'json'):
            responses[stock] = responses[stock].json
        elif hasattr(responses[stock], 'data'):
            responses[stock] = responses[stock].data

print(responses)


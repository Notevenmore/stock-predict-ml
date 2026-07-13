from controllers import OrderbookController
from flask import Flask

app = Flask(__name__)

with app.app_context():
    orderbook_controller = OrderbookController()
    responses = orderbook_controller.update_all_orderbook_data()
    if hasattr(responses, 'json'):
        responses = responses.json
    elif hasattr(responses, 'data'):
        responses = responses.data

print(responses)


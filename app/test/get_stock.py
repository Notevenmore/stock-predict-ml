from controllers import StockController
from config import config
from flask import Flask

app = Flask(__name__)

with app.app_context():
    stock_controller = StockController()
    responses = None
    responses = stock_controller.get_stock()
    if hasattr(responses, 'json'):
        responses = responses.json
    elif hasattr(responses, 'data'):
        responses = responses.data

print(responses)


from controllers import StockController
from flask import Flask

app = Flask(__name__)

with app.app_context():
    stock_controller = StockController()
    responses = stock_controller.update_all_stock_data()
    if hasattr(responses, 'json'):
        responses = responses.json
    elif hasattr(responses, 'data'):
        responses = responses.data

print(responses)


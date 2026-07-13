from controllers import ProcessedDataController
from config import config
from flask import Flask

app = Flask(__name__)

with app.app_context():
    processed_data_controller = ProcessedDataController()
    responses = {}
    for stock in config.stocks:
        responses[stock] = processed_data_controller.get_processed_data(stock)
        if hasattr(responses[stock], 'json'):
            responses[stock] = responses[stock].json
        elif hasattr(responses[stock], 'data'):
            responses[stock] = responses[stock].data

print(responses)


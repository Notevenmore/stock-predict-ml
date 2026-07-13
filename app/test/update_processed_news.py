from controllers import ProcessedDataController
from flask import Flask

app = Flask(__name__)

with app.app_context():
    processed_data_controller = ProcessedDataController()
    responses = processed_data_controller.update_all_processed_data()
    if hasattr(responses, 'json'):
        responses = responses.json
    elif hasattr(responses, 'data'):
        responses = responses.data

print(responses)


from controllers import NewsController
from flask import Flask

app = Flask(__name__)

with app.app_context():
    news_controller = NewsController()
    responses = news_controller.update_all_news_stock_data()
    if hasattr(responses, 'json'):
        responses = responses.json
    elif hasattr(responses, 'data'):
        responses = responses.data

print(responses)


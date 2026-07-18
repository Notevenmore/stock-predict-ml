from flask import Flask
from flask_migrate import Migrate
from database import db
from server import socketio
from routes import register_blueprints
from config import config

app = Flask(
    __name__,
    static_folder="data/Assets",
    static_url_path="/assets"
)

app.config["SQLALCHEMY_DATABASE_URI"] = config.SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = config.SQLALCHEMY_TRACK_MODIFICATIONS

db.init_app(app)
migrate = Migrate(app, db)

from database import StockDB

register_blueprints(app)
with app.app_context():
    from routes import initialize
    initialize()

socketio.init_app(app)

if __name__ == '__main__':
    socketio.run(app, debug=False, port=5000)
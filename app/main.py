from flask import Flask
from server import socketio
from routes import register_blueprints

app = Flask(__name__)
register_blueprints(app)

socketio.init_app(app)

if __name__ == '__main__':
    socketio.run(app, debug=False, port=5000)
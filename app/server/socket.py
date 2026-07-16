from flask_socketio import SocketIO

socketio = SocketIO(
    async_mode="threading",
    async_handlers=True,
)
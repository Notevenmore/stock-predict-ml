from .socket import socketio

class Service:
    def emit_events(self, name, data):
        socketio.emit(name, data)
    
    def start_background_task(self, task):
        socketio.start_background_task(task)
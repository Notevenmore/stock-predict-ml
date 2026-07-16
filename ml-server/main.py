import socketio

sio = socketio.Client(
    reconnection=False,
)

@sio.event
def connect():
    print("Connected")

@sio.event
def disconnect():
    print("Disconnected")

@sio.on("news_updated")
def news_updated(data):
    print(data)

@sio.on("orderbook_updated")
def orderbook_updated(data):
    print(data)

@sio.on("process_data_updated")
def process_data_updated(data):
    print(data)

@sio.on("stock_updated")
def stock_updated(data):
    print(data)

try:
    sio.connect(
        "http://127.0.0.1:5000",
        transports=["polling"]
    )
    sio.wait()
except Exception as e:
    print("Error: ", e)
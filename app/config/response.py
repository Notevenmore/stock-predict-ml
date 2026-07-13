from datetime import datetime, timezone
class Response:
    def __init__(self):
        return
    
    def success_response(self, message, data):
        if hasattr(data, "to_dict"):
            data = data.to_dict("records")
        elif hasattr(data, "tolist"):
            data = data.tolist()
        elif isinstance(data, dict):
            for key, value in data.items():
                if hasattr(value, 'to_dict'):
                    data[key] = value.to_dict('records')
                elif hasattr(value, 'tolist'):
                    data[key] = value.tolist()
        
        response = {
            "status": "SUCCESS",
            "code": 200,
            "message": message,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z"
        }

        return response
    
    def error_response(self, code, message):
        response = {
            "status": "ERROR",
            "code": code,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z"
        }

        return response
    

response = Response()
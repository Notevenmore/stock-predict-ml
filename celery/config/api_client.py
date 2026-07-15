from config import config

import requests

class ApiClient:
    def __init__(self):
        self.base_url = config.base_url
    
    def put(self, endpoint):
        response = requests.put(f"{self.base_url}{endpoint}")
        response.raise_for_status()
        result = response.json()
        
        if result["code"] != 200:
            raise Exception(result["message"])
        
        return result["data"]
    
api_client = ApiClient()
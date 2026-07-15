import os

class Config:
    def __init__(self):
        self.base_url = os.getenv("SCRAPPING_API_URL")
        self.broker_url = os.getenv("CELERY_BROKER_URL")
        self.result_backend_url = os.getenv("CELERY_RESULT_BACKEND")
        self.timezone = "Asia/Jakarta"
        self.enable_utc = False
        self.scrapping_hour= int(os.getenv("SCRAPPING_HOUR", 0))
        self.scrapping_minute = int(os.getenv("SCRAPPING_MINUTES", 0))

config = Config()
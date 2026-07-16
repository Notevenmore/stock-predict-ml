from celery import Celery
from celery.schedules import crontab
from config import config
import tasks

celery = Celery("stock_data")

celery.conf.update(
    broker_url=config.broker_url,
    result_backend=config.result_backend_url,
    timezone=config.timezone,
    enable_utc=config.enable_utc
)

celery.conf.beat_schedule = {
    "daily-update": {
        "task": "tasks.daily_update",
        "schedule": crontab(hour=config.scrapping_hour, minute=config.scrapping_minute)
    }
}
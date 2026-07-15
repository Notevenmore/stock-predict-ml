from celery import Celery
from celery.schedules import crontab
import tasks
from config import config

beat_schedule = {
    "daily-update": {
        "task": "tasks.daily_update",
        "schedule": crontab(hour=config.scrapping_hour, minute=config.scrapping_minute)
    }
}

celery = Celery("scrapper")

celery.conf.update(
    broker_url=config.broker_url,
    result_backend=config.result_backend_url,
    timezone=config.timezone,
    enable_utc=config.enable_utc,
    beat_schedule=beat_schedule
)
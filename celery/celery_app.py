from celery import Celery
from celery.schedules import crontab
import os

celery_app = Celery(
    'tasks',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Jakarta',
    enable_utc=True,
    task_track_started=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)

celery_app.conf.beat_schedule = {
    'update-all-data-midnight': {
        'task': 'tasks.update_all_data',
        'schedule': crontab(hour=0, minute=0), 
        'args': (),
    },
}

celery_app.autodiscover_tasks(['tasks'])

if __name__ == '__main__':
    celery_app.start()
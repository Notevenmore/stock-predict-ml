from celery_app import celery
from celery import chain, group, chord
from .tasks import Tasks

task_list = Tasks()

@celery.task
def update_news():
    return task_list.update_news()

@celery.task
def update_orderbook():
    return task_list.update_orderbook()

@celery.task
def update_processed_data():
    return task_list.update_processed_data()

@celery.task
def update_stock():
    return task_list.update_stock()

@celery.task
def daily_update():
    workflow = chord(
        group(
            update_orderbook.s(),
            chain(
                update_news.s(),
                update_processed_data.s()
            )
        )
    )(update_stock.s())

    return workflow.id


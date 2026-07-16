from celery import shared_task
from celery import chain, group, chord
from .tasks import Tasks

task_list = Tasks()

@shared_task
def update_news():
    return task_list.update_news()

@shared_task
def update_orderbook():
    return task_list.update_orderbook()

@shared_task
def update_processed_data():
    return task_list.update_processed_data()

@shared_task
def update_stock(_):
    return task_list.update_stock()

@shared_task
def daily_update():
    workflow = chord(
        group(
            update_orderbook.si(),
            chain(
                update_news.si(),
                update_processed_data.si()
            )   
        )
    )(update_stock.s())

    return workflow.id


from celery import Task
from celery_app import celery_app
import logging
from datetime import datetime
import traceback

from models import NewsModel, OrderbookModel, ProcessedDataModel, StockModel
from repository import repository

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UpdateDataTask(Task):
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(f"❌ Task {self.name} gagal: {str(exc)}")
        logger.error(traceback.format_exc())
        
    def on_success(self, retval, task_id, args, kwargs):
        logger.info(f"✅ Task {self.name} berhasil dijalankan")
        

@celery_app.task(base=UpdateDataTask, bind=True, max_retries=3, default_retry_delay=60)
def update_all_data(self):
    logger.info(f"🔄 Memulai update semua data pada {datetime.now()}")
    
    try:
        logger.info("📰 Update News...")
        news_model = NewsModel()
        news_model.load_routine_news() 
        logger.info("✅ News selesai diupdate")

        logger.info("📊 Update Orderbook...")
        orderbook_model = OrderbookModel()
        orderbook_model.load_routine_news() 
        logger.info("✅ Orderbook selesai diupdate")
      
        logger.info("📈 Update Stock (OHLCV & IHSG)...")
        stock_model = StockModel()
        stock_model.load_routine_stock()  
        logger.info("✅ Stock selesai diupdate")
        
        logger.info("🧠 Update Processed Data (Embedding)...")
        processed_model = ProcessedDataModel()
        processed_model.load_routine_news() 
        logger.info("✅ Processed Data selesai diupdate")
        
        # ============================================
        # STEP 5: Reload data di repository (jika perlu)
        # ============================================
        # Repository udah ke-load otomatis dari model
        # Tapi kalau mau force reload:
        # from repository import repository
        # repository.news.load_news_data()
        # repository.orderbook.load_orderbook_data()
        # repository.stock.load_ohlcv()
        # repository.stock.load_ihsg()
        # repository.processed.load_embedded_data()
        
        logger.info(f"🎉 SEMUA UPDATE SELESAI pada {datetime.now()}")
        
        return {
            'status': 'success',
            'timestamp': str(datetime.now()),
            'message': 'Semua data berhasil diupdate'
        }
        
    except Exception as e:
        logger.error(f"❌ Error update data: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Retry dengan delay 60 detik
        self.retry(exc=e, countdown=60)
        raise


@celery_app.task(base=UpdateDataTask, bind=True)
def update_news_only(self):
    try:
        news_model = NewsModel()
        news_model.load_routine_news()
        return {'status': 'success', 'message': 'News updated'}
    except Exception as e:
        self.retry(exc=e, countdown=30)
        raise


@celery_app.task(base=UpdateDataTask, bind=True)
def update_orderbook_only(self):
    logger.info(f"🔄 Update Orderbook saja pada {datetime.now()}")
    try:
        orderbook_model = OrderbookModel()
        orderbook_model.load_routine_news()
        return {'status': 'success', 'message': 'Orderbook updated'}
    except Exception as e:
        self.retry(exc=e, countdown=30)
        raise


@celery_app.task(base=UpdateDataTask, bind=True)
def update_stock_only(self):
    logger.info(f"🔄 Update Stock saja pada {datetime.now()}")
    try:
        stock_model = StockModel()
        stock_model.load_routine_stock()
        return {'status': 'success', 'message': 'Stock updated'}
    except Exception as e:
        self.retry(exc=e, countdown=30)
        raise


@celery_app.task(base=UpdateDataTask, bind=True)
def update_processed_only(self):
    logger.info(f"🔄 Update Processed Data saja pada {datetime.now()}")
    try:
        processed_model = ProcessedDataModel()
        processed_model.load_routine_news()
        return {'status': 'success', 'message': 'Processed Data updated'}
    except Exception as e:
        self.retry(exc=e, countdown=30)
        raise
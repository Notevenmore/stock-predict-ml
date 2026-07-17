# Stock Data Mining

Project ini merupakan project untuk mendukung pengumpulan data-data berita, data-data _orderbook_, dan data-data teknikal emiten

Project ini akan digunakan oleh **Stock-ML Prediction** untuk memprediksi kenaikan ataupun penurunan harga saham yang ada di emiten IHSG.

Project ini masih dalam pengembangan dan dapat dioptimalisasi data nya dengan menambahkan pengumpulan data berita International (saat ini, data berita sebatas berita dalam negeri)

## Installation Guide

### <STOCK-DATA-APP-DOCUMENTATION>

1. Inisialisasi virtual environtment untuk project terlebih dahulu

```bash
cd stock-data
python -m venv venv
```

2. Setelah itu, aktifkan virtual environtmentnya

```bash
source venv/bin/activate
```

3. Setelah mengaktifkan virtual environtment, install seluruh package yang ada di requirements.txt

```bash
pip install -r requirements.txt
```

4. Setelah melakukan inisialisasi virtual environtment, salin file .env.example dan atur data-data yang kosong (di semua folder (app, celery, ataupun ml-server) lakukan hal ini)

```bash
cd <some-project-directory>
cp .env.example .env
```

Folder App

```.env
MEDIA_KEYWORDS=
KEYWORD_NATIONAL=
KEYWORD_INTERNATIONAL=

START=
MONTHS=

CATEGORY=
LIST_MEDIA=
MEDIA_URL=
ORDERBOOK_URL=
```

Folder Celery

```.env
CELERY_BROKER_URL=
CELERY_RESULT_BACKEND=
SCRAPPING_API_URL=
SCRAPPING_MINUTES=
SCRAPPING_HOUR=
```

5. Jika ingin menambahkan package baru, jalankan command berikut diterminal

```bash
pip install <new-package>
pip freeze > requirements.txt
```

### <STOCK-DATA-CELERY-DOCUMENTATION> (For Realtime and Notify newest news, orderbook, and analyze)

6. Untuk mengaktifkan fitur realtime + scheduling data yang akan dimuat setiap hari (tepatnya di jam 12), lakukan tahapan selanjutnya

7. Aktifkan server redis (MacOS Only)

```bash
brew services start redis
```

Memastikan server redis telah berjalan

```bash
brew services list | grep redis
redis-cli ping
```

Untuk menonaktifkan:

```bash
brew services stop redis
```

Untuk restart:

```bash
brew services restart redis
```

8. Untuk melakukan pengujian fitur, jalankan

Fitur app

```bash
cd app
source ./test/test.sh
```

Fitur celery

```bash
cd celery
python -m test.workflow
```

9. Jalankan celery worker, beat dan server

```bash
   cd celery
   celery -A celery_app worker --loglevel=info
```

```bash
   cd celery
   celery -A celery_app beat --loglevel=info
```

```bash
   cd app
   python main.py
```

10. Jalankan ML Server

```bash
    cd ml-server
    python main.py
```

## Arsitektur Sistem

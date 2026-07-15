**Stock Data Mining**
Project ini merupakan project untuk mendukung pengumpulan data-data berita, data-data _orderbook_, dan data-data teknikal emiten

Project ini akan digunakan oleh **Stock-ML Prediction** untuk memprediksi kenaikan ataupun penurunan harga saham yang ada di emiten IHSG.

Project ini masih dalam pengembangan dan dapat dioptimalisasi data nya dengan menambahkan pengumpulan data berita International (saat ini, data berita sebatas berita dalam negeri)

**Installation Guide <STOCK-DATA-APP-DOCUMENTATION>**

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

4. Setelah melakukan inisialisasi virtual environtment, salin file .env.example dan atur data-data yang kosong

```bash
cp .env.example .env
```

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

CELERY_BROKER_URL=
CELERY_RESULT_BACKEND=
```

5. Jika ingin menambahkan package baru, jalankan command berikut diterminal

```bash
pip install <new-package>
pip freeze > requirements.txt
```

**Instalation Guide <STOCK-DATA-CELERY-DOCUMENTATION> (For Realtime and Notify newest news, orderbook, and analyze)**

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

```bash
cd app
source ./test/test.sh
```

9. Jalankan celery
   celery -A celery_app worker --loglevel=info
   celery -A celery_app beat --loglevel=info
   python app.py

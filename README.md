**Stock Data Mining**
Project ini merupakan project untuk mendukung pengumpulan data-data berita, data-data _orderbook_, dan data-data teknikal emiten

Project ini akan digunakan oleh **Stock-ML Prediction** untuk memprediksi kenaikan ataupun penurunan harga saham yang ada di emiten IHSG.

Project ini masih dalam pengembangan dan dapat dioptimalisasi data nya dengan menambahkan pengumpulan data berita International (saat ini, data berita sebatas berita dalam negeri)

**Panduan Penginstalan**

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
```

5. Jika ingin menambahkan package baru, jalankan command berikut diterminal

```bash
pip install <new-package>
pip freeze > requirements.txt
```

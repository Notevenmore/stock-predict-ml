import main
from database import db, StockDB

stocks = [
    {
        "name": "Bakrie & Brothers",
        "code": "BNBR",
        "image": "assets/bnbr-logo.png",
        "categories": [
            "Perdagangan",
            "Konstruksi",
            "Pertanian",
            "Pertambangan",
            "ENRG",
            "BLD",
            "BWPT",
            "BTEL",
            "BUMI",
            "VKTR"
        ]
    },
    {
        "name": "Bumi Resources",
        "code": "BUMI",
        "image": "assets/bumi-logo.png",
        "categories": [
            "Pertambangan",
            "Mineral",
            "Energy",
            "Energi",
            "Sumber Daya Alam",
            "SDA",
            "migas",
            "gas",
            "Minyak"
        ]
    },
    {
        "name": "Minna Padi Investama Sekuritas",
        "code": "PADI",
        "image": "assets/padi-logo.png",
        "categories": [
            "Keuangan"
        ]
    }
]

with main.app.app_context():
    for item in stocks:

        stock = StockDB.query.filter_by(code=item["code"]).first()

        if stock:
            print(f'{item["code"]} sudah ada.')
            continue

        db.session.add(StockDB(**item))

    db.session.commit()

print("Seed selesai.")
from database.db import db
from sqlalchemy.dialects.postgresql import ARRAY

class StockDB(db.Model):
    __tablename__ = "stock"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    code = db.Column(db.String(20), nullable=False, unique=True)
    image = db.Column(db.Text)
    categories = db.Column(ARRAY(db.String), nullable=False, default=list)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "image": self.image,
            "categories": self.categories
        }
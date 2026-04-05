from app.database import SessionLocal
from app.models.category import Category

default_categories = [
    {"name": "Makanan", "icon": "🍱"},
    {"name": "Minuman", "icon": "🥤"},
    {"name": "Snack", "icon": "🍿"},
    {"name": "Dessert", "icon": "🍰"},
    {"name": "Sarapan", "icon": "🍳"},
    {"name": "Lainnya", "icon": "🍽️"},
]

db = SessionLocal()
try:
    existing = db.query(Category).count()
    if existing > 0:
        print(f"Already have {existing} categories, skipping.")
    else:
        for c in default_categories:
            db.add(Category(**c))
        db.commit()
        print(f"Seeded {len(default_categories)} categories!")
finally:
    db.close()

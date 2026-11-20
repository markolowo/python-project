# =====================================================================
# ФАЙЛ: app/seed.py — СТАРТОВЫЕ ТОВАРЫ
# ---------------------------------------------------------------------
# Если товаров в базе нет — добавить 5 стартовых (вызывается при запуске приложения и в тестах).
# =====================================================================

from sqlalchemy import func, select

from app.models import Product

STARTING_PRODUCTS = [
    {"name": "Ноутбук", "price": 75000, "category": "electronics", "stock": 5},
    {"name": "Наушники", "price": 4500, "category": "electronics", "stock": 20},
    {"name": "Футболка", "price": 1200, "category": "clothing", "stock": 50},
    {"name": "Учебник Python", "price": 1800, "category": "books", "stock": 10},
    {"name": "Кофе в зёрнах", "price": 950, "category": "food", "stock": 30},
]


def add_starting_products(session):
    products_count = session.scalar(select(func.count()).select_from(Product))
    if products_count == 0:
        session.add_all([Product(**data) for data in STARTING_PRODUCTS])
        session.commit()

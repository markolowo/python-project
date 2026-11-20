# =====================================================================
# ФАЙЛ: app/seed.py — СТАРТОВЫЕ ДАННЫЕ
# ---------------------------------------------------------------------
# add_starting_products — 5 товаров, если каталог пуст.
# add_admin — администратор, если его ещё нет. Пароль хэшируется так же, как при регистрации.
# =====================================================================

from sqlalchemy import func, select

from app.config import ADMIN_EMAIL, ADMIN_PASSWORD
from app.models import Product, User, UserRole
from app.security import hash_password

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


def add_admin(session):
    email = ADMIN_EMAIL.lower()
    if session.scalar(select(User).where(User.email == email)) is None:
        admin = User(
            name="Администратор",
            email=email,
            hashed_password=hash_password(ADMIN_PASSWORD),
            role=UserRole.ADMIN.value,
        )
        session.add(admin)
        session.commit()

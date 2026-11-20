# =====================================================================
# ФАЙЛ: app/main.py — ПРИЛОЖЕНИЕ
# ---------------------------------------------------------------------
# Новое в КТ 3: lifespan — код при запуске: создать таблицы (create_all) и добавить стартовые товары.
# Добавлен роутер заказов и тег «Заказы».
# =====================================================================

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import Base, SessionLocal, engine
from app.routers import orders, products, users
from app.seed import add_starting_products

tags_metadata = [
    {"name": "Товары", "description": "Каталог: просмотр с фильтрами, создание, изменение и удаление товаров."},
    {"name": "Пользователи", "description": "Регистрация и управление пользователями магазина."},
    {"name": "Заказы", "description": "Оформление и просмотр заказов (связь пользователей и товаров)."},
]


@asynccontextmanager
async def lifespan(app):
    Base.metadata.create_all(engine)
    with SessionLocal() as session:
        add_starting_products(session)
    yield


app = FastAPI(
    title="Каталог магазина API",
    description=(
        "REST API интернет-магазина: каталог товаров с фильтрацией и пагинацией, пользователи и их заказы. "
        "Все ответы и ошибки — в формате JSON; при ошибке возвращается поле `detail` с описанием."
    ),
    version="1.1.0",
    openapi_tags=tags_metadata,
    lifespan=lifespan,
)

app.include_router(products.router)
app.include_router(users.router)
app.include_router(orders.router)

# =====================================================================
# ФАЙЛ: app/main.py — ПРИЛОЖЕНИЕ: CORS, ОГРАНИЧЕНИЕ ЧАСТОТЫ, РОУТЕРЫ
# ---------------------------------------------------------------------
# Новое в КТ 4:
#   app.state.limiter + обработчик RateLimitExceeded — подключение slowapi; превышение -> ответ 429
#   CORSMiddleware(allow_origins=CORS_ORIGINS) — пункт 6: ЯВНЫЙ список сайтов (по умолчанию http://localhost:3000),
#     а не "*". Браузер разрешит JavaScript с других сайтов читать ответы API только с этих адресов
#   add_admin — при запуске создаётся администратор из ADMIN_EMAIL/ADMIN_PASSWORD
#   роутер auth — регистрация и вход
# =====================================================================

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import CORS_ORIGINS
from app.database import Base, SessionLocal, engine
from app.limiter import limiter
from app.routers import auth, orders, products, users
from app.seed import add_admin, add_starting_products

tags_metadata = [
    {"name": "Аутентификация", "description": "Регистрация, вход (JWT) и текущий пользователь."},
    {"name": "Товары", "description": "Каталог: смотреть могут все, менять — только администратор."},
    {"name": "Пользователи", "description": "Пользователи магазина: список и удаление — только администратор."},
    {"name": "Заказы", "description": "Оформление и просмотр заказов (связь пользователей и товаров)."},
]


@asynccontextmanager
async def lifespan(app):
    Base.metadata.create_all(engine)
    with SessionLocal() as session:
        add_starting_products(session)
        add_admin(session)
    yield


app = FastAPI(
    title="Каталог магазина API",
    description=(
        "REST API интернет-магазина: каталог товаров с фильтрацией и пагинацией, пользователи и их заказы. "
        "Вход — через `/auth/login` (кнопка **Authorize**), токен JWT. "
        "Все ответы и ошибки — в формате JSON; при ошибке возвращается поле `detail` с описанием."
    ),
    version="1.2.0",
    openapi_tags=tags_metadata,
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth.router)
app.include_router(products.router)
app.include_router(users.router)
app.include_router(orders.router)

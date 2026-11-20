# КТ 5: подключены роутер tasks (статус задач Celery) и GraphQL на /graphql.
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

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import CORS_ORIGINS
from app.database import Base, SessionLocal, engine, get_session
from app.graphql_api import graphql_router            # КТ 5: GraphQL
from app.limiter import limiter
from app.routers import auth, orders, products, tasks, users   # tasks — КТ 5: статус фоновых задач
from app.seed import add_admin, add_starting_products

tags_metadata = [
    {"name": "Аутентификация", "description": "Регистрация, вход (JWT) и текущий пользователь."},
    {"name": "Товары", "description": "Каталог: смотреть могут все, менять — только администратор."},
    {"name": "Пользователи", "description": "Пользователи магазина: список и удаление — только администратор."},
    {"name": "Заказы", "description": "Оформление и просмотр заказов (связь пользователей и товаров)."},
    {"name": "Фоновые задачи", "description": "Статус задач Celery (например, отправки чека)."},
    {"name": "Служебное", "description": "Проверка, что приложение работает и видит базу данных."},
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
        "Фоновые задачи — Celery + Redis. GraphQL-запросы к каталогу — по адресу `/graphql`. "
        "Все ответы и ошибки — в формате JSON; при ошибке возвращается поле `detail` с описанием."
    ),
    version="1.4.0",
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
app.include_router(tasks.router)
# GraphQL на /graphql. include_in_schema=False — не показывать в Swagger: у GraphQL свой интерфейс
# GraphiQL (открывается по GET /graphql в браузере) и своя документация
app.include_router(graphql_router, prefix="/graphql", include_in_schema=False)


# ---- КТ 6: проверка работоспособности ----
# Выполняет простейший запрос SELECT 1 — если база недоступна, будет ошибка 500.
# dialect.name — какая база подключена: "sqlite" локально, "postgresql" в Docker.
# Так на защите видно, что контейнер приложения действительно подключился к контейнеру db.
# Этот же адрес удобен хостингу (Railway) для проверки, что сервис жив.
@app.get("/health", tags=["Служебное"], summary="Проверка работы и подключения к базе")
def health(session: Session = Depends(get_session)):
    session.execute(text("SELECT 1"))
    return {"status": "ok", "database": session.get_bind().dialect.name}

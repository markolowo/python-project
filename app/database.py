# =====================================================================
# ФАЙЛ: app/database.py — ПОДКЛЮЧЕНИЕ К БАЗЕ (SQLAlchemy)
# ---------------------------------------------------------------------
# engine — «двигатель» подключения к базе; адрес из переменной DATABASE_URL, по умолчанию файл shop.db (SQLite).
# SessionLocal — фабрика сессий. Сессия — «разговор» с базой: через неё читаем и сохраняем объекты.
# get_session — зависимость FastAPI (Depends): открывает сессию на время запроса и закрывает после.
# Base — базовый класс всех моделей (стиль SQLAlchemy 2.0, как в теме 14).
# =====================================================================

import os

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./shop.db")


class Base(DeclarativeBase):
    pass


def make_engine(url):
    if url.startswith("sqlite"):
        engine = create_engine(url, connect_args={"check_same_thread": False})

        # check_same_thread=False — FastAPI обрабатывает запросы в разных потоках, SQLite иначе ругается.
        # Особенность SQLite: встроенная функция lower() переводит в нижний регистр ТОЛЬКО латиницу.
        # Тогда поиск «НОУТ» не нашёл бы «Ноутбук». Подменяем lower на питоновский str.lower (понимает кириллицу).
        # В PostgreSQL (КТ 6) это не нужно — там lower() работает с любыми буквами.
        @event.listens_for(engine, "connect")
        def use_python_lower(dbapi_connection, connection_record):
            dbapi_connection.create_function("lower", 1, lambda value: value.lower() if value else value)

        return engine

    return create_engine(url)


engine = make_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def get_session():
    with SessionLocal() as session:
        yield session

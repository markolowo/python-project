# =====================================================================
# ФАЙЛ: tests/conftest.py — ТЕСТОВАЯ БАЗА
# ---------------------------------------------------------------------
# Для каждого теста — новая база SQLite во временной папке tmp_path (тесты не мешают друг другу).
# app.dependency_overrides[get_session] — подмена зависимости: приложение в тестах берёт сессию
# тестовой базы, а не рабочей shop.db.
# =====================================================================

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_session, make_engine
from app.main import app
from app.seed import add_starting_products


@pytest.fixture
def client(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path / 'test.db'}")
    TestSession = sessionmaker(bind=engine, expire_on_commit=False)
    Base.metadata.create_all(engine)

    with TestSession() as session:
        add_starting_products(session)

    def get_test_session():
        with TestSession() as session:
            yield session

    app.dependency_overrides[get_session] = get_test_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    engine.dispose()

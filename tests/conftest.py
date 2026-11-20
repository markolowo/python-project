# =====================================================================
# ФАЙЛ: tests/conftest.py — ФИКСТУРА client
# ---------------------------------------------------------------------
# TestClient — отправляет запросы в приложение без запуска сервера (как в теме 12).
# storage.reset() — каждый тест начинает с одинаковых 5 товаров и без пользователей.
# =====================================================================

import pytest
from fastapi.testclient import TestClient

from app import storage
from app.main import app


@pytest.fixture
def client():
    storage.reset()
    with TestClient(app) as test_client:
        yield test_client

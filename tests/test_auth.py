# =====================================================================
# ФАЙЛ: tests/test_auth.py — ВСЕ СЦЕНАРИИ ИЗ «ТРЕБОВАНИЙ К ДЕМОНСТРАЦИИ»
# ---------------------------------------------------------------------
# регистрация (201) и повтор email (409) | пароль хранится хэшем $2b$ | вход -> JWT (три части через точку)
# неверный пароль (401) | защищённый эндпоинт с токеном (200), без токена и с поддельным (401)
# admin-эндпоинт от user (403) и от admin (200) | шестая попытка входа подряд (429) | CORS только для своего origin
# =====================================================================

from sqlalchemy import select

from app.database import get_session
from app.main import app
from app.models import User
from conftest import login, register


def test_register_returns_user_with_role_user(client):
    response = register(client, "ivan@example.com")

    assert response.status_code == 201
    assert response.json()["role"] == "user"
    assert "password" not in response.text


def test_password_is_stored_as_bcrypt_hash(client):
    register(client, "ivan@example.com", password="secret123")

    session = next(app.dependency_overrides[get_session]())
    user = session.scalar(select(User).where(User.email == "ivan@example.com"))

    assert user.hashed_password != "secret123"
    assert user.hashed_password.startswith("$2b$")


def test_register_same_email_returns_409(client):
    register(client, "ivan@example.com")

    response = register(client, "IVAN@example.com")

    assert response.status_code == 409


def test_login_returns_jwt(client):
    register(client, "ivan@example.com")

    response = login(client, "ivan@example.com", "secret123")

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"].count(".") == 2


def test_login_with_wrong_password_returns_401(client):
    register(client, "ivan@example.com")

    assert login(client, "ivan@example.com", "wrong-password").status_code == 401


def test_protected_endpoint_with_token(client, anna):
    response = client.get("/auth/me", headers=anna["headers"])

    assert response.status_code == 200
    assert response.json()["email"] == "anna@example.com"


def test_protected_endpoint_without_token_returns_401(client):
    assert client.get("/auth/me").status_code == 401


def test_protected_endpoint_with_fake_token_returns_401(client):
    response = client.get("/auth/me", headers={"Authorization": "Bearer not.a.token"})

    assert response.status_code == 401


def test_admin_endpoint_for_user_returns_403(client, anna):
    assert client.get("/users", headers=anna["headers"]).status_code == 403


def test_admin_endpoint_for_admin_returns_200(client, admin_headers):
    assert client.get("/users", headers=admin_headers).status_code == 200


def test_sixth_login_attempt_returns_429(client):
    register(client, "ivan@example.com")

    statuses = [login(client, "ivan@example.com", "wrong").status_code for _ in range(6)]

    assert statuses == [401, 401, 401, 401, 401, 429]


def test_cors_allows_only_configured_origin(client):
    allowed = client.options(
        "/products", headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "GET"}
    )
    foreign = client.options(
        "/products", headers={"Origin": "http://evil.example", "Access-Control-Request-Method": "GET"}
    )

    assert allowed.headers.get("access-control-allow-origin") == "http://localhost:3000"
    assert "access-control-allow-origin" not in foreign.headers

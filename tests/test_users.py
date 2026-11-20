# =====================================================================
# ФАЙЛ: tests/test_users.py — ПОЛЬЗОВАТЕЛИ
# ---------------------------------------------------------------------
# Email в нижнем регистре, 422 за неверный email и короткий пароль,
# пользователь видит только себя, удалять может только admin.
# =====================================================================

from conftest import register


def test_email_is_stored_in_lowercase(client):
    response = register(client, "Anna@Example.com")

    assert response.json()["email"] == "anna@example.com"


def test_invalid_email_returns_422(client):
    assert register(client, "not-an-email").status_code == 422


def test_short_password_returns_422(client):
    assert register(client, "ivan@example.com", password="123").status_code == 422


def test_user_sees_only_himself(client, anna, admin_headers):
    other_id = register(client, "other@example.com").json()["id"]

    assert client.get(f"/users/{anna['id']}", headers=anna["headers"]).status_code == 200
    assert client.get(f"/users/{other_id}", headers=anna["headers"]).status_code == 403
    assert client.get(f"/users/{other_id}", headers=admin_headers).status_code == 200


def test_only_admin_deletes_users(client, anna, admin_headers):
    assert client.delete(f"/users/{anna['id']}", headers=anna["headers"]).status_code == 403
    assert client.delete(f"/users/{anna['id']}", headers=admin_headers).status_code == 204

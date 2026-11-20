# =====================================================================
# ФАЙЛ: tests/test_users.py — ТЕСТЫ ПОЛЬЗОВАТЕЛЕЙ
# ---------------------------------------------------------------------
# Email в нижнем регистре, 409 за повтор email (даже в другом регистре), 422 за неверный email, удаление.
# =====================================================================

def test_create_user_stores_email_in_lowercase(client):
    response = client.post("/users", json={"name": "Анна", "email": "Anna@Example.com"})

    assert response.status_code == 201
    assert response.json()["email"] == "anna@example.com"


def test_duplicate_email_returns_409(client):
    client.post("/users", json={"name": "Анна", "email": "anna@example.com"})

    response = client.post("/users", json={"name": "Другая Анна", "email": "ANNA@example.com"})

    assert response.status_code == 409


def test_invalid_email_returns_422(client):
    response = client.post("/users", json={"name": "Анна", "email": "not-an-email"})

    assert response.status_code == 422


def test_get_and_delete_user(client):
    user_id = client.post("/users", json={"name": "Иван", "email": "ivan@example.com"}).json()["id"]

    assert client.get(f"/users/{user_id}").json()["name"] == "Иван"
    assert client.delete(f"/users/{user_id}").status_code == 204
    assert client.get(f"/users/{user_id}").status_code == 404

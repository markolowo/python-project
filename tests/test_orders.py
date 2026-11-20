# =====================================================================
# ФАЙЛ: tests/test_orders.py — ТЕСТЫ ЗАКАЗОВ И СВЯЗЕЙ
# ---------------------------------------------------------------------
# Сумма считается сервером; у пользователя несколько заказов; товар знает свои заказы и покупателей;
# ошибки 404/400/422; удаление пользователя удаляет его заказы, но не товары.
# =====================================================================

import pytest


@pytest.fixture
def anna(client):
    return client.post("/users", json={"name": "Анна", "email": "anna@example.com"}).json()


def test_order_total_is_calculated_by_server(client, anna):
    response = client.post("/orders", json={"user_id": anna["id"], "product_ids": [1, 2]})

    assert response.status_code == 201
    assert response.json()["total_price"] == 75000 + 4500
    assert [product["name"] for product in response.json()["products"]] == ["Ноутбук", "Наушники"]


def test_user_has_many_orders(client, anna):
    client.post("/orders", json={"user_id": anna["id"], "product_ids": [1]})
    client.post("/orders", json={"user_id": anna["id"], "product_ids": [2, 3]})

    orders = client.get(f"/users/{anna['id']}/orders").json()

    assert len(orders) == 2
    assert all(order["user_id"] == anna["id"] for order in orders)


def test_product_knows_its_orders_and_buyers(client, anna):
    client.post("/orders", json={"user_id": anna["id"], "product_ids": [1, 2]})
    client.post("/orders", json={"user_id": anna["id"], "product_ids": [2, 3]})

    orders_with_headphones = client.get("/products/2/orders").json()

    assert len(orders_with_headphones) == 2
    assert orders_with_headphones[0]["user"]["name"] == "Анна"


def test_order_with_unknown_user_returns_404(client):
    response = client.post("/orders", json={"user_id": 999, "product_ids": [1]})

    assert response.status_code == 404


def test_order_with_unknown_product_returns_404(client, anna):
    response = client.post("/orders", json={"user_id": anna["id"], "product_ids": [1, 999]})

    assert response.status_code == 404


def test_order_with_repeated_product_returns_400(client, anna):
    response = client.post("/orders", json={"user_id": anna["id"], "product_ids": [1, 1]})

    assert response.status_code == 400


def test_empty_order_returns_422(client, anna):
    response = client.post("/orders", json={"user_id": anna["id"], "product_ids": []})

    assert response.status_code == 422


def test_deleting_user_deletes_orders(client, anna):
    order_id = client.post("/orders", json={"user_id": anna["id"], "product_ids": [1]}).json()["id"]

    client.delete(f"/users/{anna['id']}")

    assert client.get(f"/orders/{order_id}").status_code == 404
    assert client.get("/products/1").status_code == 200

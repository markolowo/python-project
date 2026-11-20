# =====================================================================
# ФАЙЛ: tests/test_orders.py — ЗАКАЗЫ С ВХОДОМ
# ---------------------------------------------------------------------
# Заказ оформляется с токеном и принадлежит вошедшему; без входа 401; чужой заказ — 403 для user, 200 для admin.
# =====================================================================

from conftest import register, auth_header


def create_order(client, user, product_ids):
    return client.post("/orders", json={"product_ids": product_ids}, headers=user["headers"])


def test_order_total_is_calculated_by_server(client, anna):
    response = create_order(client, anna, [1, 2])

    assert response.status_code == 201
    assert response.json()["user_id"] == anna["id"]
    assert response.json()["total_price"] == 75000 + 4500
    assert [product["name"] for product in response.json()["products"]] == ["Ноутбук", "Наушники"]


def test_user_has_many_orders(client, anna):
    create_order(client, anna, [1])
    create_order(client, anna, [2, 3])

    orders = client.get(f"/users/{anna['id']}/orders", headers=anna["headers"]).json()

    assert len(orders) == 2
    assert all(order["user_id"] == anna["id"] for order in orders)


def test_product_knows_its_orders_and_buyers(client, anna):
    create_order(client, anna, [1, 2])
    create_order(client, anna, [2, 3])

    orders_with_headphones = client.get("/products/2/orders").json()

    assert len(orders_with_headphones) == 2
    assert orders_with_headphones[0]["user"]["name"] == "Анна"


def test_order_requires_login(client):
    assert client.post("/orders", json={"product_ids": [1]}).status_code == 401


def test_order_with_unknown_product_returns_404(client, anna):
    assert create_order(client, anna, [1, 999]).status_code == 404


def test_order_with_repeated_product_returns_400(client, anna):
    assert create_order(client, anna, [1, 1]).status_code == 400


def test_empty_order_returns_422(client, anna):
    assert create_order(client, anna, []).status_code == 422


def test_user_cannot_see_other_users_order(client, anna, admin_headers):
    order_id = create_order(client, anna, [1]).json()["id"]
    register(client, "other@example.com")
    other_headers = auth_header(client, "other@example.com", "secret123")

    assert client.get(f"/orders/{order_id}", headers=other_headers).status_code == 403
    assert client.get(f"/orders/{order_id}", headers=admin_headers).status_code == 200


def test_deleting_user_deletes_orders(client, anna, admin_headers):
    order_id = create_order(client, anna, [1]).json()["id"]

    client.delete(f"/users/{anna['id']}", headers=admin_headers)

    assert client.get(f"/orders/{order_id}", headers=admin_headers).status_code == 404
    assert client.get("/products/1").status_code == 200

# =====================================================================
# ФАЙЛ: tests/test_products.py — ТОВАРЫ
# ---------------------------------------------------------------------
# Фильтры и поиск — без входа. Создание/изменение/удаление — с токеном admin; user получает 403, аноним 401.
# =====================================================================

def test_list_returns_starting_products(client):
    response = client.get("/products")

    assert response.status_code == 200
    assert response.json()["total"] == 5


def test_filters_are_combined(client):
    response = client.get("/products", params={"category": "electronics", "max_price": 10000})

    names = [product["name"] for product in response.json()["items"]]
    assert names == ["Наушники"]


def test_search_ignores_case(client):
    response = client.get("/products", params={"search": "НОУТ"})

    assert response.json()["items"][0]["name"] == "Ноутбук"


def test_pagination_keeps_total(client):
    response = client.get("/products", params={"skip": 2, "limit": 2})

    assert len(response.json()["items"]) == 2
    assert response.json()["total"] == 5


def test_create_product(client, admin_headers):
    response = client.post(
        "/products", json={"name": "Мышка", "price": 1500, "category": "electronics"}, headers=admin_headers
    )

    assert response.status_code == 201
    assert response.json()["stock"] == 0


def test_duplicate_name_returns_409(client, admin_headers):
    response = client.post(
        "/products", json={"name": "НОУТБУК", "price": 1, "category": "electronics"}, headers=admin_headers
    )

    assert response.status_code == 409


def test_invalid_product_returns_422(client, admin_headers):
    response = client.post("/products", json={"name": "A", "price": -5, "category": "cars"}, headers=admin_headers)

    assert response.status_code == 422


def test_patch_changes_only_given_fields(client, admin_headers):
    response = client.patch("/products/1", json={"price": 70000}, headers=admin_headers)

    assert response.json()["price"] == 70000
    assert response.json()["name"] == "Ноутбук"


def test_unknown_product_returns_404(client):
    assert client.get("/products/999").status_code == 404


def test_delete_product(client, admin_headers):
    assert client.delete("/products/1", headers=admin_headers).status_code == 204
    assert client.get("/products/1").status_code == 404


def test_user_cannot_change_catalog(client, anna):
    new_product = {"name": "Мышка", "price": 1, "category": "food"}

    assert client.post("/products", json=new_product, headers=anna["headers"]).status_code == 403
    assert client.delete("/products/1", headers=anna["headers"]).status_code == 403


def test_anonymous_cannot_change_catalog(client):
    assert client.delete("/products/1").status_code == 401

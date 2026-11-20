# =====================================================================
# ФАЙЛ: tests/test_graphql.py — ТЕСТЫ GraphQL
# ---------------------------------------------------------------------
# GraphQL-запрос — это POST /graphql с JSON {"query": "..."}. Ответ обычно 200: успех — в поле data,
# ошибки — в поле errors. Главный тест — два запроса к одному полю products с разным набором полей.
# =====================================================================

def graphql(client, query):
    response = client.post("/graphql", json={"query": query})
    assert response.status_code == 200
    assert "errors" not in response.json(), response.json()
    return response.json()["data"]


def test_short_query_returns_only_names(client):
    data = graphql(client, "{ products { name } }")

    assert data["products"][0] == {"name": "Ноутбук"}
    assert len(data["products"]) == 5


def test_detailed_query_to_same_field_returns_more_data(client, anna):
    client.post("/orders", json={"product_ids": [1, 2]}, headers=anna["headers"])

    data = graphql(
        client,
        '{ products(category: "electronics") { name price orders { id totalPrice buyer { name } } } }',
    )

    laptop = data["products"][0]
    assert laptop["name"] == "Ноутбук"
    assert laptop["price"] == 75000
    assert laptop["orders"][0]["buyer"]["name"] == "Анна"
    assert len(data["products"]) == 2


def test_filter_by_max_price(client):
    data = graphql(client, "{ products(maxPrice: 1500) { name price } }")

    assert all(product["price"] <= 1500 for product in data["products"])


def test_single_product_and_missing_product(client):
    data = graphql(client, "{ found: product(id: 1) { name } missing: product(id: 999) { name } }")

    assert data == {"found": {"name": "Ноутбук"}, "missing": None}


def test_unknown_field_returns_error(client):
    response = client.post("/graphql", json={"query": "{ products { color } }"})

    assert "errors" in response.json()

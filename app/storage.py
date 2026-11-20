# =====================================================================
# ФАЙЛ: app/storage.py — ХРАНИЛИЩЕ В ПАМЯТИ
# ---------------------------------------------------------------------
# Пока без базы данных (база появится в КТ 3): словари products и users.
# next_id — выдаёт следующий номер. reset — очистить и заполнить 5 стартовыми товарами
# (вызывается при запуске и перед каждым тестом).
# =====================================================================

products = {}
users = {}
counters = {"product": 0, "user": 0}


def next_id(kind):
    counters[kind] += 1
    return counters[kind]


def reset():
    products.clear()
    users.clear()
    counters["product"] = 0
    counters["user"] = 0

    starting_products = [
        {"name": "Ноутбук", "price": 75000, "category": "electronics", "stock": 5},
        {"name": "Наушники", "price": 4500, "category": "electronics", "stock": 20},
        {"name": "Футболка", "price": 1200, "category": "clothing", "stock": 50},
        {"name": "Учебник Python", "price": 1800, "category": "books", "stock": 10},
        {"name": "Кофе в зёрнах", "price": 950, "category": "food", "stock": 30},
    ]
    for data in starting_products:
        product_id = next_id("product")
        products[product_id] = {"id": product_id, **data}


reset()

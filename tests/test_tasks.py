# =====================================================================
# ФАЙЛ: tests/test_tasks.py — ТЕСТЫ ФОНОВОЙ ЗАДАЧИ
# ---------------------------------------------------------------------
# Задача в тестах выполняется сразу (eager), поэтому статус уже SUCCESS. Живой сценарий
# PENDING -> STARTED -> SUCCESS с настоящим воркером показан в ЗАЩИТА.md.
# Проверяем: 202 и task_id, результат, неизвестная задача = PENDING, 404, 403 на чужой заказ, 401 без входа.
# =====================================================================

from conftest import auth_header, register


def create_order(client, user, product_ids):
    return client.post("/orders", json={"product_ids": product_ids}, headers=user["headers"]).json()


def test_send_receipt_returns_task_id_with_202(client, anna):
    order = create_order(client, anna, [1, 2])

    response = client.post(f"/orders/{order['id']}/send-receipt", headers=anna["headers"])

    assert response.status_code == 202
    assert response.json()["task_id"]


def test_task_status_returns_result_when_ready(client, anna):
    order = create_order(client, anna, [1])
    task_id = client.post(f"/orders/{order['id']}/send-receipt", headers=anna["headers"]).json()["task_id"]

    response = client.get(f"/tasks/{task_id}", headers=anna["headers"])

    assert response.json()["status"] == "SUCCESS"
    assert response.json()["result"]["sent_to"] == "anna@example.com"
    assert response.json()["result"]["order_id"] == order["id"]


def test_unknown_task_is_pending(client, anna):
    response = client.get("/tasks/no-such-task", headers=anna["headers"])

    assert response.json() == {"task_id": "no-such-task", "status": "PENDING", "result": None}


def test_receipt_for_unknown_order_returns_404(client, anna):
    assert client.post("/orders/999/send-receipt", headers=anna["headers"]).status_code == 404


def test_receipt_for_other_users_order_returns_403(client, anna):
    order = create_order(client, anna, [1])
    register(client, "other@example.com")
    other_headers = auth_header(client, "other@example.com", "secret123")

    response = client.post(f"/orders/{order['id']}/send-receipt", headers=other_headers)

    assert response.status_code == 403


def test_task_endpoints_require_login(client):
    assert client.post("/orders/1/send-receipt").status_code == 401
    assert client.get("/tasks/any").status_code == 401

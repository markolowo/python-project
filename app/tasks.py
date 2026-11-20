# =====================================================================
# ФАЙЛ: app/tasks.py — ФОНОВАЯ ЗАДАЧА (пункт 1 задания)
# ---------------------------------------------------------------------
# @celery_app.task — превращает обычную функцию в задачу Celery: её можно вызвать через .delay()
# из FastAPI, а выполнит её воркер.
# send_receipt имитирует долгую отправку письма: time.sleep(RECEIPT_SECONDS) — 5 секунд «отправки».
# Результат (словарь) Celery сохранит в Redis — его вернёт GET /tasks/{id}.
# В реальном проекте здесь было бы подключение к почтовому серверу (smtplib) или сервису рассылок.
# =====================================================================

import time
from datetime import datetime, timezone

from app.celery_app import celery_app
from app.config import RECEIPT_SECONDS


@celery_app.task(name="send_receipt")
def send_receipt(order_id, email, total_price):
    time.sleep(RECEIPT_SECONDS)

    return {
        "order_id": order_id,
        "sent_to": email,
        "message": f"Чек по заказу №{order_id} на сумму {total_price:.2f} ₽ отправлен на {email}",
        "sent_at": datetime.now(timezone.utc).isoformat(),
    }

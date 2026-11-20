# =====================================================================
# ФАЙЛ: app/celery_app.py — ПРИЛОЖЕНИЕ CELERY
# ---------------------------------------------------------------------
# Celery — система фоновых задач (тема 21). Схема:
#   FastAPI --.delay()--> Redis (брокер, очередь) --> воркер Celery выполняет --> Redis (результат) --> GET /tasks/{id}
# Воркер — ОТДЕЛЬНЫЙ процесс, запуск:
#   celery -A app.celery_app worker --pool=solo --loglevel=info
#   --pool=solo — обязательно на Windows (обычный режим Celery на Windows не работает)
# include=["app.tasks"] — где лежат задачи
# task_store_eager_result — в тестах (eager-режим) результат тоже сохраняется, и GET /tasks/{id} его видит
# task_track_started — показывать STARTED, пока задача выполняется (иначе сразу PENDING -> SUCCESS)
# result_expires — результаты хранятся час, потом удаляются из Redis
# =====================================================================

from celery import Celery

from app.config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND, CELERY_TASK_ALWAYS_EAGER

celery_app = Celery(
    "shop",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=["app.tasks"],
)

celery_app.conf.update(
    task_always_eager=CELERY_TASK_ALWAYS_EAGER,
    task_store_eager_result=True,
    task_track_started=True,
    result_expires=3600,
)

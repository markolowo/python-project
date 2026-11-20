# =====================================================================
# ФАЙЛ: app/routers/tasks.py — СТАТУС ЗАДАЧИ (пункт 3 задания)
# ---------------------------------------------------------------------
# AsyncResult(task_id) — «справка» о задаче по id: читает статус и результат из хранилища (Redis).
# task.status: PENDING (в очереди или неизвестна) -> STARTED (воркер выполняет) -> SUCCESS / FAILURE
# task.successful() — готово без ошибок, task.result — то, что вернула функция задачи
# task.failed() — задача упала, task.result — исключение (отдаём его текст)
# Требует вход (dependencies=[Depends(get_current_user)]).
# =====================================================================

from celery.result import AsyncResult
from fastapi import APIRouter, Depends

from app.celery_app import celery_app
from app.dependencies import get_current_user
from app.schemas import ErrorResponse, TaskInfo

router = APIRouter(prefix="/tasks", tags=["Фоновые задачи"])


@router.get(
    "/{task_id}",
    response_model=TaskInfo,
    responses={401: {"model": ErrorResponse, "description": "Нет токена или он недействителен"}},
    summary="Статус фоновой задачи",
    description=(
        "Показывает состояние задачи Celery: **PENDING** — ещё в очереди, **STARTED** — выполняется, "
        "**SUCCESS** — готово (в поле `result` — результат), **FAILURE** — ошибка. "
        "Celery не различает «ещё не начата» и «такой задачи нет» — для неизвестного id тоже будет PENDING."
    ),
    dependencies=[Depends(get_current_user)],
)
def get_task_status(task_id: str):
    task = AsyncResult(task_id, app=celery_app)

    if task.successful():
        result = task.result
    elif task.failed():
        result = {"error": str(task.result)}
    else:
        result = None

    return {"task_id": task_id, "status": task.status, "result": result}

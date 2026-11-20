# =====================================================================
# ФАЙЛ: app/routers/orders.py — ЗАКАЗЫ (с входом)
# ---------------------------------------------------------------------
# Изменение КТ 4: покупатель — ВОШЕДШИЙ пользователь (current_user из токена), а не user_id из тела запроса.
# Иначе любой мог бы оформить заказ от чужого имени.
# Чужой заказ видит только admin (ensure_owner_or_admin).
# =====================================================================

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_session
from app.dependencies import ensure_owner_or_admin, get_current_user
from app.models import Order, Product, User
from app.schemas import ErrorResponse, OrderCreate, TaskInfo
from app.schemas import Order as OrderSchema
from app.tasks import send_receipt                 # КТ 5: фоновая задача Celery

router = APIRouter(prefix="/orders", tags=["Заказы"])

NOT_FOUND = {404: {"model": ErrorResponse, "description": "Заказ или товар не найден"}}
AUTH_ERRORS = {
    401: {"model": ErrorResponse, "description": "Нет токена или он недействителен"},
    403: {"model": ErrorResponse, "description": "Чужой заказ"},
}


@router.post(
    "",
    response_model=OrderSchema,
    status_code=status.HTTP_201_CREATED,
    responses={**NOT_FOUND, **AUTH_ERRORS, 400: {"model": ErrorResponse, "description": "Товары в заказе повторяются"}},
    summary="Оформить заказ",
    description=(
        "Создаёт заказ **от имени вошедшего пользователя** из списка товаров. `total_price` **считается сервером** "
        "как сумма текущих цен товаров — передавать её не нужно. Каждый товар указывается один раз."
    ),
)
def create_order(
    data: OrderCreate, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)
):
    if len(set(data.product_ids)) != len(data.product_ids):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Товары в заказе не должны повторяться")

    products = session.scalars(select(Product).where(Product.id.in_(data.product_ids))).all()
    if len(products) != len(data.product_ids):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Некоторые товары не найдены")

    order = Order(
        user=current_user,
        products=list(products),
        total_price=sum(product.price for product in products),
    )
    session.add(order)
    session.commit()
    return order


@router.get(
    "/{order_id}",
    response_model=OrderSchema,
    responses={**NOT_FOUND, **AUTH_ERRORS},
    summary="Получить заказ с товарами",
    description="Свой заказ видит владелец, чужой — только admin.",
)
def get_order(order_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    order = session.get(Order, order_id)
    if order is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Заказ не найден")
    ensure_owner_or_admin(current_user, order.user_id)
    return order


# ---- КТ 5: ФОНОВАЯ ЗАДАЧА ----
# Пункт 2 задания: вызов задачи через .delay() из эндпоинта.
# 202 Accepted — «принято к выполнению»: работа ещё НЕ сделана, но поставлена в очередь
@router.post(
    "/{order_id}/send-receipt",
    response_model=TaskInfo,
    status_code=status.HTTP_202_ACCEPTED,
    responses={**NOT_FOUND, **AUTH_ERRORS},
    summary="Отправить чек на почту (фоновая задача)",
    description=(
        "Ставит в очередь Celery задачу отправки чека и **сразу** отвечает 202 с `task_id`, не дожидаясь отправки. "
        "Сама отправка идёт в воркере несколько секунд. Статус и результат — `GET /tasks/{task_id}`."
    ),
)
def send_order_receipt(
    order_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)
):
    order = session.get(Order, order_id)
    if order is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Заказ не найден")
    ensure_owner_or_admin(current_user, order.user_id)   # чек по чужому заказу отправить нельзя

    # .delay(...) НЕ выполняет задачу здесь, а кладёт сообщение «выполни send_receipt с такими данными»
    # в Redis и сразу возвращает объект с id задачи. Поэтому ответ приходит мгновенно (~0.2 с),
    # хотя сама отправка занимает 5 секунд — её выполнит отдельный процесс-воркер.
    # Передаём простые данные (id, email, сумму), а не объект order: в очередь можно положить только
    # то, что превращается в JSON
    task = send_receipt.delay(order.id, order.user.email, order.total_price)
    return {"task_id": task.id, "status": task.status}

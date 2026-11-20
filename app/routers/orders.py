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
from app.schemas import ErrorResponse, OrderCreate
from app.schemas import Order as OrderSchema

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

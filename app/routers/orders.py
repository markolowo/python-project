# =====================================================================
# ФАЙЛ: app/routers/orders.py — ЗАКАЗЫ
# ---------------------------------------------------------------------
# POST /orders — оформить заказ: user_id + список product_ids. Сумму total_price считает сервер.
# Order(user=user, products=[...]) — связи заполняются как обычные атрибуты Python,
# SQLAlchemy сама проставит user_id и запишет пары в order_products.
# GET /orders/{id} — заказ со списком товаров (связь заказ -> товары).
# =====================================================================

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_session
from app.models import Order, Product, User
from app.schemas import ErrorResponse, OrderCreate
from app.schemas import Order as OrderSchema

router = APIRouter(prefix="/orders", tags=["Заказы"])

NOT_FOUND = {404: {"model": ErrorResponse, "description": "Заказ, пользователь или товар не найден"}}


@router.post(
    "",
    response_model=OrderSchema,
    status_code=status.HTTP_201_CREATED,
    responses={**NOT_FOUND, 400: {"model": ErrorResponse, "description": "Товары в заказе повторяются"}},
    summary="Оформить заказ",
    description=(
        "Создаёт заказ пользователя из списка товаров. `total_price` **считается сервером** как сумма "
        "текущих цен товаров — передавать её не нужно. Каждый товар указывается один раз."
    ),
)
def create_order(data: OrderCreate, session: Session = Depends(get_session)):
    user = session.get(User, data.user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Пользователь не найден")

    if len(set(data.product_ids)) != len(data.product_ids):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Товары в заказе не должны повторяться")

    products = session.scalars(select(Product).where(Product.id.in_(data.product_ids))).all()
    if len(products) != len(data.product_ids):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Некоторые товары не найдены")

    order = Order(user=user, products=list(products), total_price=sum(product.price for product in products))
    session.add(order)
    session.commit()
    return order


@router.get("/{order_id}", response_model=OrderSchema, responses=NOT_FOUND, summary="Получить заказ с товарами")
def get_order(order_id: int, session: Session = Depends(get_session)):
    order = session.get(Order, order_id)
    if order is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Заказ не найден")
    return order

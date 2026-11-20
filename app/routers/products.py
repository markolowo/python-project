# =====================================================================
# ФАЙЛ: app/routers/products.py — ТОВАРЫ (теперь в базе)
# ---------------------------------------------------------------------
# Вместо словаря — запросы SQLAlchemy: select(Product).where(...) собирает SQL по частям.
# ilike — поиск подстроки без учёта регистра. func.count — сколько найдено.
# Новое: GET /products/{id}/orders — связь многие-ко-многим в ОБРАТНУЮ сторону (товар -> заказы -> покупатель).
# Все запросы через ORM — значения передаются параметрами, SQL-инъекция невозможна.
# =====================================================================

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_session
from app.models import Product
from app.schemas import ErrorResponse, OrderOfProduct, ProductCreate, ProductList, ProductUpdate
from app.schemas import Product as ProductSchema

router = APIRouter(prefix="/products", tags=["Товары"])

NOT_FOUND = {404: {"model": ErrorResponse, "description": "Товар не найден"}}
NAME_TAKEN = {409: {"model": ErrorResponse, "description": "Товар с таким названием уже есть"}}


def find_product(session, product_id):
    product = session.get(Product, product_id)
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Товар не найден")
    return product


def ensure_name_is_free(session, name, except_id=None):
    query = select(Product).where(func.lower(Product.name) == name.lower())
    if except_id is not None:
        query = query.where(Product.id != except_id)
    if session.scalar(query) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Товар с таким названием уже есть")


@router.get(
    "",
    response_model=ProductList,
    summary="Список товаров с фильтрами",
    description=(
        "Возвращает товары каталога. Все фильтры необязательные и **объединяются через И**: "
        "например, `category=electronics&max_price=10000` вернёт только электронику дешевле 10 000. "
        "`search` ищет подстроку в названии без учёта регистра. "
        "Пагинация: `skip` — сколько пропустить, `limit` — сколько вернуть. "
        "Поле `total` в ответе — число всех найденных товаров **до** пагинации."
    ),
)
def list_products(
    category: str | None = Query(default=None, description="Категория", examples=["electronics"]),
    min_price: float | None = Query(default=None, ge=0, description="Минимальная цена (включительно)"),
    max_price: float | None = Query(default=None, ge=0, description="Максимальная цена (включительно)"),
    search: str | None = Query(default=None, min_length=1, description="Часть названия"),
    skip: int = Query(default=0, ge=0, description="Сколько товаров пропустить"),
    limit: int = Query(default=10, ge=1, le=100, description="Сколько товаров вернуть (1–100)"),
    session: Session = Depends(get_session),
):
    query = select(Product)

    if category is not None:
        query = query.where(Product.category == category)
    if min_price is not None:
        query = query.where(Product.price >= min_price)
    if max_price is not None:
        query = query.where(Product.price <= max_price)
    if search is not None:
        query = query.where(Product.name.ilike(f"%{search}%"))

    total = session.scalar(select(func.count()).select_from(query.subquery()))
    items = session.scalars(query.order_by(Product.id).offset(skip).limit(limit)).all()

    return {"items": items, "total": total}


@router.get("/{product_id}", response_model=ProductSchema, responses=NOT_FOUND, summary="Получить товар по id")
def get_product(product_id: int, session: Session = Depends(get_session)):
    return find_product(session, product_id)


@router.get(
    "/{product_id}/orders",
    response_model=list[OrderOfProduct],
    responses=NOT_FOUND,
    summary="Заказы, в которые входит товар",
    description="Связь многие-ко-многим в обратную сторону: от товара к заказам (и их покупателям).",
)
def get_product_orders(product_id: int, session: Session = Depends(get_session)):
    return find_product(session, product_id).orders


@router.post(
    "",
    response_model=ProductSchema,
    status_code=status.HTTP_201_CREATED,
    responses=NAME_TAKEN,
    summary="Создать товар",
    description=(
        "Добавляет товар в каталог. Название должно быть **уникальным без учёта регистра**: "
        "если уже есть «Ноутбук», то «НОУТБУК» создать нельзя — вернётся 409. "
        "Если `stock` не передан, товар создаётся с нулевым остатком."
    ),
)
def create_product(data: ProductCreate, session: Session = Depends(get_session)):
    ensure_name_is_free(session, data.name)
    product = Product(**data.model_dump())
    session.add(product)
    session.commit()
    return product


@router.patch(
    "/{product_id}",
    response_model=ProductSchema,
    responses={**NOT_FOUND, **NAME_TAKEN},
    summary="Частично изменить товар",
    description=(
        "Меняет только переданные поля, остальные остаются прежними. "
        "При смене названия проверяется уникальность среди **других** товаров."
    ),
)
def update_product(product_id: int, data: ProductUpdate, session: Session = Depends(get_session)):
    product = find_product(session, product_id)
    changes = data.model_dump(exclude_unset=True, exclude_none=True)

    if "name" in changes:
        ensure_name_is_free(session, changes["name"], except_id=product_id)

    for field, value in changes.items():
        setattr(product, field, value)
    session.commit()
    return product


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=NOT_FOUND,
    summary="Удалить товар",
)
def delete_product(product_id: int, session: Session = Depends(get_session)):
    session.delete(find_product(session, product_id))
    session.commit()

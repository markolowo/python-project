# =====================================================================
# ФАЙЛ: app/routers/products.py — ЭНДПОИНТЫ ТОВАРОВ (тег «Товары»)
# ---------------------------------------------------------------------
# APIRouter(prefix="/products", tags=["Товары"]) — все маршруты файла начинаются с /products
# и попадают в группу «Товары» (пункт 3).
# У каждого маршрута summary — короткое название в списке /docs (пункт 4).
# description — подробное объяснение там, где логика неочевидна (пункт 5): фильтры, уникальность названия, PATCH.
# responses={404: ...} — описать в документации возможные ошибки.
# HTTPException — вернуть клиенту ошибку с кодом и текстом (404 не найдено, 409 конфликт).
# =====================================================================

from fastapi import APIRouter, HTTPException, Query, status

from app import storage
from app.schemas import ErrorResponse, Product, ProductCreate, ProductList, ProductUpdate

router = APIRouter(prefix="/products", tags=["Товары"])

NOT_FOUND = {404: {"model": ErrorResponse, "description": "Товар не найден"}}
NAME_TAKEN = {409: {"model": ErrorResponse, "description": "Товар с таким названием уже есть"}}


def find_product(product_id):
    product = storage.products.get(product_id)
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Товар не найден")
    return product


# Проверка уникальности названия без учёта регистра. except_id — не сравнивать товар с самим собой (для PATCH)
def ensure_name_is_free(name, except_id=None):
    for product in storage.products.values():
        if product["name"].lower() == name.lower() and product["id"] != except_id:
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
):
    # Начинаем со всех товаров и по очереди применяем фильтры, которые прислали (логика «И»)
    found = list(storage.products.values())

    if category is not None:
        found = [product for product in found if product["category"] == category]
    if min_price is not None:
        found = [product for product in found if product["price"] >= min_price]
    if max_price is not None:
        found = [product for product in found if product["price"] <= max_price]
    if search is not None:
        found = [product for product in found if search.lower() in product["name"].lower()]

    # Срез [skip:skip+limit] — пагинация; total — сколько найдено ДО пагинации
    return {"items": found[skip:skip + limit], "total": len(found)}


@router.get("/{product_id}", response_model=Product, responses=NOT_FOUND, summary="Получить товар по id")
def get_product(product_id: int):
    return find_product(product_id)


@router.post(
    "",
    response_model=Product,
    status_code=status.HTTP_201_CREATED,
    responses=NAME_TAKEN,
    summary="Создать товар",
    description=(
        "Добавляет товар в каталог. Название должно быть **уникальным без учёта регистра**: "
        "если уже есть «Ноутбук», то «НОУТБУК» создать нельзя — вернётся 409. "
        "Если `stock` не передан, товар создаётся с нулевым остатком."
    ),
)
def create_product(data: ProductCreate):
    ensure_name_is_free(data.name)
    product_id = storage.next_id("product")
    product = {"id": product_id, **data.model_dump()}
    storage.products[product_id] = product
    return product


@router.patch(
    "/{product_id}",
    response_model=Product,
    responses={**NOT_FOUND, **NAME_TAKEN},
    summary="Частично изменить товар",
    description=(
        "Меняет только переданные поля, остальные остаются прежними. "
        "При смене названия проверяется уникальность среди **других** товаров."
    ),
)
def update_product(product_id: int, data: ProductUpdate):
    product = find_product(product_id)
    # exclude_unset — только поля, которые клиент прислал; exclude_none — игнорировать null
    changes = data.model_dump(exclude_unset=True, exclude_none=True)

    if "name" in changes:
        ensure_name_is_free(changes["name"], except_id=product_id)

    product.update(changes)
    return product


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=NOT_FOUND,
    summary="Удалить товар",
)
def delete_product(product_id: int):
    find_product(product_id)
    del storage.products[product_id]

# =====================================================================
# ФАЙЛ: app/schemas.py — МОДЕЛИ PYDANTIC (что приходит в запросе и что уходит в ответе)
# ---------------------------------------------------------------------
# FastAPI по этим моделям: 1) проверяет входящий JSON (ошибка -> 422), 2) рисует схемы в /docs.
# Пункт 6 задания: Field(description=..., examples=[...]) — описание и пример значения поля.
# Описаны и с примерами: name, price, category, stock (товар), name, email (пользователь), id, total, detail.
# Ограничения: min_length/max_length — длина строки, gt=0 — строго больше нуля, ge=0 — не меньше нуля,
# pattern — регулярное выражение (только одна из 4 категорий).
# =====================================================================

from pydantic import BaseModel, ConfigDict, EmailStr, Field

CATEGORIES = ["electronics", "clothing", "books", "food"]


class ProductCreate(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=100,
        description="Название товара. Должно быть уникальным в каталоге (без учёта регистра).",
        examples=["Ноутбук Lenovo IdeaPad 5"],
    )
    price: float = Field(
        gt=0,
        description="Цена в рублях, строго больше нуля.",
        examples=[54990.0],
    )
    category: str = Field(
        pattern="^(electronics|clothing|books|food)$",
        description="Категория товара: electronics, clothing, books или food.",
        examples=["electronics"],
    )
    stock: int = Field(
        default=0,
        ge=0,
        description="Количество на складе. Если не указано — 0.",
        examples=[12],
    )


# Для PATCH: все поля необязательные (None по умолчанию) — меняем только присланные
class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100, examples=["Ноутбук Lenovo IdeaPad 5 Pro"])
    price: float | None = Field(default=None, gt=0, examples=[59990.0])
    category: str | None = Field(default=None, pattern="^(electronics|clothing|books|food)$", examples=["electronics"])
    stock: int | None = Field(default=None, ge=0, examples=[5])


# Ответ = поля создания + id. Наследование: Product получает все поля ProductCreate
class Product(ProductCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Уникальный номер товара, присваивается автоматически.", examples=[1])


class ProductList(BaseModel):
    items: list[Product]
    total: int = Field(description="Сколько всего товаров подходит под фильтры (без учёта пагинации).", examples=[42])


class UserCreate(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=100,
        description="Имя пользователя для отображения.",
        examples=["Анна Петрова"],
    )
    email: EmailStr = Field(
        description="Электронная почта. Должна быть уникальной: второй пользователь с той же почтой не создаётся.",
        examples=["anna@example.com"],
    )


class User(UserCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Уникальный номер пользователя.", examples=[1])


# ---- КТ 3: заказы ----
# OrderCreate — что присылает клиент: кто покупает и какие товары (min_length=1 — хотя бы один)
class OrderCreate(BaseModel):
    user_id: int = Field(description="Кто оформляет заказ (id пользователя).", examples=[1])
    product_ids: list[int] = Field(
        min_length=1,
        description="id товаров в заказе, без повторов. Сумма заказа считается автоматически.",
        examples=[[1, 2]],
    )


# Товар внутри заказа — только id, название и цена
class ProductInOrder(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    price: float


# Заказ в ответе. from_attributes=True — Pydantic умеет читать объекты SQLAlchemy (order.products и т.д.)
class Order(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    total_price: float = Field(description="Сумма цен товаров на момент оформления.", examples=[79500.0])
    user_id: int
    products: list[ProductInOrder]


# Заказ, показанный со стороны товара: с покупателем (user)
class OrderOfProduct(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    total_price: float
    user: User


# Формат ошибки (так отвечает HTTPException) — нужен, чтобы ошибки 404/409 были описаны в /docs
class ErrorResponse(BaseModel):
    detail: str = Field(description="Описание ошибки.", examples=["Товар не найден"])

# =====================================================================
# ФАЙЛ: app/schemas.py — МОДЕЛИ PYDANTIC
# ---------------------------------------------------------------------
# Товары — как в КТ 2. Новое в КТ 4:
#   UserRegister — данные регистрации: name, email (EmailStr проверяет формат), password 8–72 символа
#     (72 — предел алгоритма bcrypt)
#   User — ответ о пользователе: id, name, email, role. Пароля и хэша в ответе НЕТ
#   Token — ответ входа: access_token + token_type="bearer" (формат OAuth2)
#   OrderCreate — теперь только product_ids: покупатель берётся из токена
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


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100, examples=["Ноутбук Lenovo IdeaPad 5 Pro"])
    price: float | None = Field(default=None, gt=0, examples=[59990.0])
    category: str | None = Field(default=None, pattern="^(electronics|clothing|books|food)$", examples=["electronics"])
    stock: int | None = Field(default=None, ge=0, examples=[5])


class Product(ProductCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Уникальный номер товара, присваивается автоматически.", examples=[1])


class ProductList(BaseModel):
    items: list[Product]
    total: int = Field(description="Сколько всего товаров подходит под фильтры (без учёта пагинации).", examples=[42])


class UserRegister(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=100,
        description="Имя пользователя для отображения.",
        examples=["Анна Петрова"],
    )
    email: EmailStr = Field(
        description="Электронная почта, она же логин. Должна быть уникальной: повторная регистрация вернёт 409.",
        examples=["anna@example.com"],
    )
    password: str = Field(
        min_length=8,
        max_length=72,
        description="Пароль от 8 до 72 символов. Хранится только в виде хэша bcrypt.",
        examples=["secret123"],
    )


class User(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Уникальный номер пользователя.", examples=[1])
    name: str = Field(examples=["Анна Петрова"])
    email: str = Field(examples=["anna@example.com"])
    role: str = Field(description="Роль: user или admin.", examples=["user"])


class Token(BaseModel):
    access_token: str = Field(description="JWT. Передаётся в заголовке Authorization: Bearer <токен>.")
    token_type: str = Field(default="bearer", examples=["bearer"])


class OrderCreate(BaseModel):
    product_ids: list[int] = Field(
        min_length=1,
        description="id товаров в заказе, без повторов. Покупатель — вошедший пользователь, сумма считается автоматически.",
        examples=[[1, 2]],
    )


class ProductInOrder(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    price: float


class Order(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    total_price: float = Field(description="Сумма цен товаров на момент оформления.", examples=[79500.0])
    user_id: int
    products: list[ProductInOrder]


class OrderOfProduct(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    total_price: float
    user: User


# КТ 5: ответ о фоновой задаче — id, статус и результат (только когда готово)
class TaskInfo(BaseModel):
    task_id: str = Field(description="id фоновой задачи Celery — по нему проверяется статус.", examples=["3f2b9c1e-..."])
    status: str = Field(
        description="PENDING — ждёт или неизвестна, STARTED — выполняется, SUCCESS — готово, FAILURE — ошибка.",
        examples=["PENDING"],
    )
    result: dict | None = Field(default=None, description="Результат задачи — только при статусе SUCCESS.")


class ErrorResponse(BaseModel):
    detail: str = Field(description="Описание ошибки.", examples=["Товар не найден"])

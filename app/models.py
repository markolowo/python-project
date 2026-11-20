# =====================================================================
# ФАЙЛ: app/models.py — МОДЕЛИ (ТАБЛИЦЫ) И СВЯЗИ МЕЖДУ НИМИ
# ---------------------------------------------------------------------
# Главный файл КТ 3.
#
# Связь ОДИН-КО-МНОГИМ: User 1 — N Order (у пользователя много заказов)
#   Order.user_id = ForeignKey("users.id") — внешний ключ: колонка в таблице orders со ссылкой на users.id
#   User.orders   = relationship(back_populates="user")    — список заказов пользователя (в Python)
#   Order.user    = relationship(back_populates="orders")  — пользователь заказа (в Python)
#   back_populates связывает две стороны: добавили заказ в user.orders — у заказа сразу order.user == user
#
# Связь МНОГИЕ-КО-МНОГИМ: Order N — N Product (в заказе много товаров, товар во многих заказах)
#   Нужна ПРОМЕЖУТОЧНАЯ таблица order_products: пары (order_id, product_id)
#   relationship(secondary=order_products) — SQLAlchemy сама пишет и читает эту таблицу
#
# Mapped[int], mapped_column(...) — объявление колонок в стиле SQLAlchemy 2.0
# =====================================================================

from sqlalchemy import Column, Float, ForeignKey, Integer, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

# Промежуточная таблица: в ней нет своего класса, только две колонки-ссылки.
# primary_key на обеих — одна и та же пара (заказ, товар) не может повториться.
# ondelete="CASCADE" — удалили заказ или товар -> строки связи удаляются тоже
order_products = Table(
    "order_products",
    Base.metadata,
    Column("order_id", ForeignKey("orders.id", ondelete="CASCADE"), primary_key=True),
    Column("product_id", ForeignKey("products.id", ondelete="CASCADE"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True)

    # cascade="all, delete-orphan" — удаляем пользователя -> удаляются и его заказы
    orders: Mapped[list["Order"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    total_price: Mapped[float] = mapped_column(Float)   # поле из задания: Order(id, total_price)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    user: Mapped["User"] = relationship(back_populates="orders")
    products: Mapped[list["Product"]] = relationship(secondary=order_products, back_populates="orders")


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    price: Mapped[float] = mapped_column(Float)
    category: Mapped[str] = mapped_column(String(20))
    stock: Mapped[int] = mapped_column(Integer, default=0)

    orders: Mapped[list["Order"]] = relationship(secondary=order_products, back_populates="products")

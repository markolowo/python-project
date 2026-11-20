# =====================================================================
# ФАЙЛ: app/models.py — МОДЕЛИ И СВЯЗИ
# ---------------------------------------------------------------------
# Связи — как в КТ 3 (подробно — в Объяснении КТ 3).
# Новое в КТ 4 (пункт 1 задания):
#   UserRole — перечисление ролей: user и admin (str, enum.Enum — значения хранятся строками)
#   User.hashed_password — ХЭШ пароля (сам пароль нигде не хранится)
#   User.role — роль, по умолчанию user
#   order_by=... в связях — списки всегда упорядочены по id
# =====================================================================

import enum

from sqlalchemy import Column, Float, ForeignKey, Integer, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

order_products = Table(
    "order_products",
    Base.metadata,
    Column("order_id", ForeignKey("orders.id", ondelete="CASCADE"), primary_key=True),
    Column("product_id", ForeignKey("products.id", ondelete="CASCADE"), primary_key=True),
)


class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default=UserRole.USER.value)

    orders: Mapped[list["Order"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", order_by="Order.id"
    )


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    total_price: Mapped[float] = mapped_column(Float)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    user: Mapped["User"] = relationship(back_populates="orders")
    products: Mapped[list["Product"]] = relationship(
        secondary=order_products, back_populates="orders", order_by="Product.id"
    )


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    price: Mapped[float] = mapped_column(Float)
    category: Mapped[str] = mapped_column(String(20))
    stock: Mapped[int] = mapped_column(Integer, default=0)

    orders: Mapped[list["Order"]] = relationship(
        secondary=order_products, back_populates="products", order_by="Order.id"
    )

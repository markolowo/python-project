# =====================================================================
# ФАЙЛ: demo_relations.py — ДЕМО СВЯЗЕЙ (из КТ 3)
# ---------------------------------------------------------------------
# В КТ 4 у пользователя обязателен hashed_password, поэтому демо-пользователь создаётся с паролем.
# =====================================================================

from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import Base, make_engine
from app.models import Order, Product, User
from app.security import hash_password

DEMO_DATABASE = Path(__file__).parent / "demo_relations.db"


def create_data(session):
    user = User(name="Иван Петров", email="ivan@example.com", hashed_password=hash_password("demo12345"))

    laptop = Product(name="Ноутбук", price=75000, category="electronics", stock=5)
    mouse = Product(name="Мышь", price=1500, category="electronics", stock=40)
    bag = Product(name="Сумка для ноутбука", price=3000, category="clothing", stock=12)

    first_order = Order(user=user, products=[laptop, mouse])
    second_order = Order(user=user, products=[mouse, bag])

    for order in [first_order, second_order]:
        order.total_price = sum(product.price for product in order.products)

    session.add_all([user, laptop, mouse, bag, first_order, second_order])
    session.commit()


def show_user_to_orders(session):
    print("1) Пользователь → его заказы (один-ко-многим)")
    user = session.scalars(select(User).where(User.email == "ivan@example.com")).one()
    for order in user.orders:
        print(f"   {user.name}: заказ №{order.id} на {order.total_price:.0f} ₽")


def show_order_to_user(session):
    print("2) Заказ → пользователь (обратная сторона)")
    for order in session.scalars(select(Order).order_by(Order.id)):
        print(f"   заказ №{order.id} оформил {order.user.name}")


def show_order_to_products(session):
    print("3) Заказ → товары (многие-ко-многим)")
    for order in session.scalars(select(Order).order_by(Order.id)):
        names = ", ".join(product.name for product in order.products)
        print(f"   заказ №{order.id}: {names}")


def show_product_to_orders(session):
    print("4) Товар → заказы (обратная сторона)")
    for product in session.scalars(select(Product).order_by(Product.id)):
        order_numbers = ", ".join(f"№{order.id}" for order in product.orders)
        print(f"   {product.name}: в заказах {order_numbers}")


def main():
    DEMO_DATABASE.unlink(missing_ok=True)
    engine = make_engine(f"sqlite:///{DEMO_DATABASE}")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        create_data(session)

    with Session(engine) as session:
        show_user_to_orders(session)
        show_order_to_user(session)
        show_order_to_products(session)
        show_product_to_orders(session)

    engine.dispose()


if __name__ == "__main__":
    main()

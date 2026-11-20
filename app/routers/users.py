# =====================================================================
# ФАЙЛ: app/routers/users.py — ПОЛЬЗОВАТЕЛИ (теперь в базе)
# ---------------------------------------------------------------------
# Новое: GET /users/{id}/orders — связь один-ко-многим (пользователь -> его заказы).
# user.orders — SQLAlchemy сама выполнит запрос к таблице orders по user_id.
# =====================================================================

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_session
from app.models import User
from app.schemas import ErrorResponse, Order, UserCreate
from app.schemas import User as UserSchema

router = APIRouter(prefix="/users", tags=["Пользователи"])

NOT_FOUND = {404: {"model": ErrorResponse, "description": "Пользователь не найден"}}


def find_user(session, user_id):
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Пользователь не найден")
    return user


@router.get("", response_model=list[UserSchema], summary="Список пользователей")
def list_users(session: Session = Depends(get_session)):
    return session.scalars(select(User).order_by(User.id)).all()


@router.get("/{user_id}", response_model=UserSchema, responses=NOT_FOUND, summary="Получить пользователя по id")
def get_user(user_id: int, session: Session = Depends(get_session)):
    return find_user(session, user_id)


@router.get(
    "/{user_id}/orders",
    response_model=list[Order],
    responses=NOT_FOUND,
    summary="Заказы пользователя",
    description="Связь один-ко-многим: от пользователя к его заказам, у каждого заказа — список товаров.",
)
def get_user_orders(user_id: int, session: Session = Depends(get_session)):
    return find_user(session, user_id).orders


@router.post(
    "",
    response_model=UserSchema,
    status_code=status.HTTP_201_CREATED,
    responses={409: {"model": ErrorResponse, "description": "Email уже занят"}},
    summary="Зарегистрировать пользователя",
    description=(
        "Создаёт пользователя. Email проверяется на **уникальность без учёта регистра**: "
        "`Anna@Example.com` и `anna@example.com` считаются одним адресом, повторная регистрация вернёт 409. "
        "Email сохраняется в нижнем регистре."
    ),
)
def create_user(data: UserCreate, session: Session = Depends(get_session)):
    email = data.email.lower()
    if session.scalar(select(User).where(User.email == email)) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Email уже занят")

    user = User(name=data.name, email=email)
    session.add(user)
    session.commit()
    return user


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=NOT_FOUND,
    summary="Удалить пользователя",
    description="Удаляет пользователя **вместе со всеми его заказами** (каскадное удаление).",
)
def delete_user(user_id: int, session: Session = Depends(get_session)):
    session.delete(find_user(session, user_id))
    session.commit()

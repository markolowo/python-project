# =====================================================================
# ФАЙЛ: app/routers/users.py — ПОЛЬЗОВАТЕЛИ (с правами)
# ---------------------------------------------------------------------
# admin_only = require_role(UserRole.ADMIN) — пункт 5: список и удаление пользователей только для admin
#   (dependencies=[Depends(admin_only)] — проверка без использования результата в функции).
# GET /users/{id} и /users/{id}/orders — свои данные видит владелец, чужие — только admin (ensure_owner_or_admin).
# POST /users убран: пользователи создаются через /auth/register.
# =====================================================================

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_session
from app.dependencies import ensure_owner_or_admin, get_current_user, require_role
from app.models import User, UserRole
from app.schemas import ErrorResponse, Order
from app.schemas import User as UserSchema

router = APIRouter(prefix="/users", tags=["Пользователи"])

NOT_FOUND = {404: {"model": ErrorResponse, "description": "Пользователь не найден"}}
AUTH_ERRORS = {
    401: {"model": ErrorResponse, "description": "Нет токена или он недействителен"},
    403: {"model": ErrorResponse, "description": "Недостаточно прав"},
}

admin_only = require_role(UserRole.ADMIN)


def find_user(session, user_id):
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Пользователь не найден")
    return user


@router.get(
    "",
    response_model=list[UserSchema],
    responses=AUTH_ERRORS,
    summary="Список пользователей (только admin)",
    dependencies=[Depends(admin_only)],
)
def list_users(session: Session = Depends(get_session)):
    return session.scalars(select(User).order_by(User.id)).all()


@router.get(
    "/{user_id}",
    response_model=UserSchema,
    responses={**NOT_FOUND, **AUTH_ERRORS},
    summary="Получить пользователя по id",
    description="Обычный пользователь может получить только **себя**, admin — любого.",
)
def get_user(user_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    ensure_owner_or_admin(current_user, user_id)
    return find_user(session, user_id)


@router.get(
    "/{user_id}/orders",
    response_model=list[Order],
    responses={**NOT_FOUND, **AUTH_ERRORS},
    summary="Заказы пользователя",
    description=(
        "Связь один-ко-многим: от пользователя к его заказам, у каждого заказа — список товаров. "
        "Свои заказы видит владелец, чужие — только admin."
    ),
)
def get_user_orders(
    user_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)
):
    ensure_owner_or_admin(current_user, user_id)
    return find_user(session, user_id).orders


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={**NOT_FOUND, **AUTH_ERRORS},
    summary="Удалить пользователя (только admin)",
    description="Удаляет пользователя **вместе со всеми его заказами** (каскадное удаление).",
    dependencies=[Depends(admin_only)],
)
def delete_user(user_id: int, session: Session = Depends(get_session)):
    session.delete(find_user(session, user_id))
    session.commit()

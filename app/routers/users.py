# =====================================================================
# ФАЙЛ: app/routers/users.py — ЭНДПОИНТЫ ПОЛЬЗОВАТЕЛЕЙ (тег «Пользователи»)
# ---------------------------------------------------------------------
# Главная неочевидная логика — уникальность email без учёта регистра (описана в description, пункт 5).
# EmailStr в модели сам проверяет формат почты (нужен пакет email-validator).
# =====================================================================

from fastapi import APIRouter, HTTPException, status

from app import storage
from app.schemas import ErrorResponse, User, UserCreate

router = APIRouter(prefix="/users", tags=["Пользователи"])

NOT_FOUND = {404: {"model": ErrorResponse, "description": "Пользователь не найден"}}


def find_user(user_id):
    user = storage.users.get(user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Пользователь не найден")
    return user


@router.get("", response_model=list[User], summary="Список пользователей")
def list_users():
    return list(storage.users.values())


@router.get("/{user_id}", response_model=User, responses=NOT_FOUND, summary="Получить пользователя по id")
def get_user(user_id: int):
    return find_user(user_id)


@router.post(
    "",
    response_model=User,
    status_code=status.HTTP_201_CREATED,
    responses={409: {"model": ErrorResponse, "description": "Email уже занят"}},
    summary="Зарегистрировать пользователя",
    description=(
        "Создаёт пользователя. Email проверяется на **уникальность без учёта регистра**: "
        "`Anna@Example.com` и `anna@example.com` считаются одним адресом, повторная регистрация вернёт 409. "
        "Email сохраняется в нижнем регистре."
    ),
)
def create_user(data: UserCreate):
    email = data.email.lower()
    for user in storage.users.values():
        if user["email"] == email:
            raise HTTPException(status.HTTP_409_CONFLICT, "Email уже занят")

    user_id = storage.next_id("user")
    user = {"id": user_id, "name": data.name, "email": email}
    storage.users[user_id] = user
    return user


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=NOT_FOUND,
    summary="Удалить пользователя",
)
def delete_user(user_id: int):
    find_user(user_id)
    del storage.users[user_id]

# =====================================================================
# ФАЙЛ: app/routers/auth.py — РЕГИСТРАЦИЯ, ВХОД, ТЕКУЩИЙ ПОЛЬЗОВАТЕЛЬ
# ---------------------------------------------------------------------
#   POST /auth/register — пункт 2 задания (passlib, 409 при занятом email)
#   POST /auth/login    — пункт 3 (OAuth2PasswordRequestForm -> JWT) + пункт 7 (slowapi, 5 в минуту)
#   GET  /auth/me       — пример защищённого эндпоинта (200 с токеном, 401 без)
# =====================================================================

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import LOGIN_RATE_LIMIT
from app.database import get_session
from app.dependencies import get_current_user
from app.limiter import limiter
from app.models import User, UserRole
from app.schemas import ErrorResponse, Token, UserRegister
from app.schemas import User as UserSchema
from app.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["Аутентификация"])


@router.post(
    "/register",
    response_model=UserSchema,           # в ответе НЕТ пароля и хэша — схема User их не содержит
    status_code=status.HTTP_201_CREATED,
    responses={409: {"model": ErrorResponse, "description": "Email уже зарегистрирован"}},
    summary="Регистрация",
    description=(
        "Создаёт пользователя с ролью **user**. Пароль сохраняется только в виде хэша bcrypt. "
        "Email уникален без учёта регистра: повторная регистрация вернёт **409**."
    ),
)
def register(data: UserRegister, session: Session = Depends(get_session)):
    # Почту храним в нижнем регистре — Anna@x.com и anna@x.com считаются одним адресом
    email = data.email.lower()

    # Проверка уникальности через ORM (select ... where) — SQL-инъекция невозможна (пункт 8)
    if session.scalar(select(User).where(User.email == email)) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Email уже зарегистрирован")

    # Роль при регистрации ВСЕГДА user: стать админом через API нельзя
    user = User(name=data.name, email=email, hashed_password=hash_password(data.password), role=UserRole.USER.value)
    session.add(user)
    session.commit()
    return user


@router.post(
    "/login",
    response_model=Token,
    responses={
        401: {"model": ErrorResponse, "description": "Неверный email или пароль"},
        429: {"description": "Больше 5 попыток входа в минуту с одного адреса"},
    },
    summary="Вход (получить JWT)",
    description=(
        "Стандартная форма OAuth2: поля `username` (сюда вводится **email**) и `password`, "
        "формат `application/x-www-form-urlencoded`. Возвращает access-токен. "
        "Не больше **5 попыток в минуту** с одного IP — шестая получит **429**."
    ),
)
# slowapi: ограничение частоты (пункт 7). LOGIN_RATE_LIMIT = "5/minute" из app/config.py.
# Счётчик — по IP-адресу клиента. Шестой запрос за минуту -> 429 Too Many Requests
@limiter.limit(LOGIN_RATE_LIMIT)
def login(
    request: Request,   # slowapi нужен объект запроса, чтобы узнать IP — без этого параметра декоратор не работает
    # OAuth2PasswordRequestForm — стандартная форма входа OAuth2: поля username и password,
    # формат формы (не JSON). Именно её ждёт кнопка Authorize в /docs. В username вводим email
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
):
    user = session.scalar(select(User).where(User.email == form_data.username.lower()))

    # ОДИНАКОВАЯ ошибка для «нет такого email» и «неверный пароль» —
    # иначе по разным ответам можно выяснить, какие почты зарегистрированы
    if user is None or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Неверный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Ответ в формате OAuth2: access_token + token_type
    return {"access_token": create_access_token(user.id), "token_type": "bearer"}


@router.get(
    "/me",
    response_model=UserSchema,
    responses={401: {"model": ErrorResponse, "description": "Нет токена или он недействителен"}},
    summary="Текущий пользователь",
)
# Depends(get_current_user): без токена -> 401, с токеном -> пользователь из базы
def me(current_user: User = Depends(get_current_user)):
    return current_user

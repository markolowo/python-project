# =====================================================================
# ФАЙЛ: app/security.py — ПАРОЛИ И JWT-ТОКЕНЫ
# ---------------------------------------------------------------------
# Пункт 2 задания: хеширование пароля через passlib.
# Пункт 3 задания: JWT access-токен (библиотека python-jose, как в теме 17).
# Используется в app/routers/auth.py (регистрация и вход), app/dependencies.py (проверка токена),
# app/seed.py (пароль администратора).
# =====================================================================

from datetime import datetime, timedelta, timezone

from jose import jwt                        # python-jose: создание и проверка JWT
from passlib.context import CryptContext    # passlib: хеширование паролей

from app.config import ACCESS_TOKEN_MINUTES, ALGORITHM, SECRET_KEY

# CryptContext — «настройка хеширования»: алгоритм bcrypt.
# deprecated="auto" — если когда-то сменим алгоритм, старые хэши будут помечены как устаревшие
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Пароль -> хэш вида $2b$12$<соль><хэш>. Из хэша пароль восстановить нельзя.
# bcrypt сам добавляет случайную соль — у двух людей с одинаковым паролем хэши разные
def hash_password(password):
    return pwd_context.hash(password)


# Проверка пароля при входе: bcrypt берёт соль из сохранённого хэша, хэширует введённый пароль
# с той же солью и сравнивает. Возвращает True/False
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


# Создать JWT. Внутри (payload):
#   sub — «subject», кому выдан токен: id пользователя (строкой — так требует стандарт)
#   exp — когда истекает (через ACCESS_TOKEN_MINUTES минут, по умолчанию 30)
# Подпись делается секретом SECRET_KEY: подделать токен без секрета нельзя
def create_access_token(user_id):
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_MINUTES)
    payload = {"sub": str(user_id), "exp": expires_at}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# Прочитать id из токена. jwt.decode проверяет подпись и срок;
# если что-то не так — выбрасывает JWTError (его ловит get_current_user и отвечает 401)
def read_user_id(token):
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    return int(payload["sub"])

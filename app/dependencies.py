# =====================================================================
# ФАЙЛ: app/dependencies.py — ЗАВИСИМОСТИ БЕЗОПАСНОСТИ (Depends)
# ---------------------------------------------------------------------
# Пункт 4 задания: get_current_user — проверяет токен и возвращает пользователя (401 при ошибке).
# Пункт 5 задания: require_role — пускает только нужные роли (403 для остальных).
#
# Зависимость в FastAPI — функция, которую FastAPI вызывает ПЕРЕД обработчиком маршрута.
# Пишем в параметрах маршрута current_user: User = Depends(get_current_user) — и получаем
# готового пользователя; если токена нет — до маршрута дело не дойдёт, клиент получит 401.
# =====================================================================

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.database import get_session
from app.models import User, UserRole
from app.security import read_user_id

# Достаёт токен из заголовка Authorization: Bearer <токен>.
# Нет заголовка -> сразу 401. tokenUrl — адрес входа: по нему кнопка Authorize в /docs получает токен
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)):
    try:
        user_id = read_user_id(token)
    except (JWTError, KeyError, ValueError):
        # Подделанный, испорченный или просроченный токен.
        # Заголовок WWW-Authenticate: Bearer — по стандарту подсказывает клиенту, как авторизоваться
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Недействительный токен",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Токен верный, но пользователя могли удалить после выдачи токена
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Пользователь не найден",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


# Фабрика зависимостей (как в теме 18): require_role(UserRole.ADMIN) возвращает функцию-проверку.
# *allowed_roles — можно передать несколько ролей: require_role(UserRole.ADMIN, UserRole.USER)
# Сначала срабатывает get_current_user (нет токена -> 401), потом проверка роли (не та роль -> 403)
def require_role(*allowed_roles: UserRole):
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in [role.value for role in allowed_roles]:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Недостаточно прав")
        return current_user

    return role_checker


# Проверка «это мои данные или я админ» — для заказов и профиля.
# Обычный пользователь не должен видеть чужие заказы
def ensure_owner_or_admin(current_user, owner_id):
    if current_user.role != UserRole.ADMIN.value and current_user.id != owner_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Можно смотреть только свои данные")

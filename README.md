# Каталог магазина API

REST API интернет-магазина на FastAPI: каталог товаров с фильтрами, пользователи с ролями, заказы, фоновые задачи и GraphQL.

[![Tests](https://github.com/kiryp-coder/python-project/actions/workflows/tests.yml/badge.svg)](https://github.com/kiryp-coder/python-project/actions/workflows/tests.yml)

**Публичный адрес:** _будет указан после деплоя_ (документация — `<адрес>/docs`)

## Стек

FastAPI · Pydantic · SQLAlchemy 2 · PostgreSQL (в Docker) / SQLite (локально) · JWT (python-jose) · passlib/bcrypt · slowapi · Celery + Redis · GraphQL (strawberry) · pytest · Docker Compose · GitHub Actions

## Возможности

- Каталог: фильтры по категории и цене, поиск, пагинация; менять каталог может только администратор
- Регистрация и вход (OAuth2 + JWT), роли `user` и `admin`, ограничение входа — 5 попыток в минуту
- Заказы: связь «пользователь — заказы» (один-ко-многим) и «заказы — товары» (многие-ко-многим)
- Фоновая задача Celery: отправка чека по заказу, проверка статуса задачи
- GraphQL на `/graphql`
- Документация: Swagger UI `/docs`, ReDoc `/redoc`

## Запуск в Docker (рекомендуется)

Нужен запущенный Docker Desktop.

```bash
docker compose up --build
```

Поднимаются 4 сервиса: `app` (API), `worker` (Celery), `db` (PostgreSQL), `redis`.
Настройки — в `.env.docker` (адреса используют имена сервисов: `db`, `redis`).

- API: http://localhost:8000/docs
- Проверка: http://localhost:8000/health → `{"status": "ok", "database": "postgresql"}`
- Администратор: `admin@example.com` / `admin12345`

## Локальный запуск без Docker

```bash
python -m venv .venv
.venv\Scripts\activate            # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload     # база SQLite shop.db создаётся автоматически
```

Для фоновых задач дополнительно:
```bash
docker compose up -d redis
celery -A app.celery_app worker --pool=solo --loglevel=info    # на Windows обязательно --pool=solo
```

## Тесты

```bash
pytest -v
```
Тесты используют временную SQLite и Celery в памяти — внешние сервисы не нужны.
При каждом push в `main` тесты запускаются автоматически в GitHub Actions (`.github/workflows/tests.yml`).

## Эндпоинты

| Метод | Путь | Доступ | Описание |
|---|---|---|---|
| POST | `/auth/register` | все | Регистрация (409 — email занят) |
| POST | `/auth/login` | все | Вход, JWT (не более 5 попыток в минуту) |
| GET | `/auth/me` | вошедший | Текущий пользователь |
| GET | `/products` | все | Список: `category`, `min_price`, `max_price`, `search`, `skip`, `limit` |
| GET | `/products/{id}` | все | Товар |
| GET | `/products/{id}/orders` | все | Заказы с товаром |
| POST / PATCH / DELETE | `/products`, `/products/{id}` | admin | Изменение каталога |
| GET | `/users` | admin | Список пользователей |
| GET | `/users/{id}`, `/users/{id}/orders` | владелец или admin | Профиль и заказы |
| DELETE | `/users/{id}` | admin | Удалить пользователя с заказами |
| POST | `/orders` | вошедший | Оформить заказ |
| GET | `/orders/{id}` | владелец или admin | Заказ с товарами |
| POST | `/orders/{id}/send-receipt` | владелец или admin | Фоновая отправка чека (202 + task_id) |
| GET | `/tasks/{task_id}` | вошедший | Статус задачи: PENDING / STARTED / SUCCESS |
| GET/POST | `/graphql` | все | GraphQL (в браузере — GraphiQL) |
| GET | `/health` | все | Проверка работы и подключения к базе |

## Структура

```
app/
  main.py            приложение, CORS, ограничение частоты, /health
  config.py          настройки из переменных окружения
  database.py        подключение к базе (SQLAlchemy)
  models.py          модели User, Order, Product и связи
  schemas.py         модели Pydantic
  security.py        хэширование паролей и JWT
  dependencies.py    get_current_user, require_role
  celery_app.py      Celery; tasks.py — фоновые задачи
  graphql_api.py     GraphQL-схема
  routers/           auth, products, users, orders, tasks
tests/               pytest
Dockerfile, docker-compose.yml, .env.docker
.github/workflows/tests.yml
```

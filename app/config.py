# =====================================================================
# ФАЙЛ: app/config.py — НАСТРОЙКИ ИЗ ПЕРЕМЕННЫХ ОКРУЖЕНИЯ
# ---------------------------------------------------------------------
# os.environ.get("ИМЯ", "значение по умолчанию") — взять настройку из окружения или значение для разработки.
# На сервере (КТ 6) их задают настоящими значениями, секреты в код не пишут.
#   SECRET_KEY        — ключ подписи JWT (по умолчанию — учебный, на сервере обязательно свой!)
#   CORS_ORIGINS      — с каких сайтов браузер может обращаться к API (пункт 6), через запятую
#   LOGIN_RATE_LIMIT  — ограничение входа "5/minute" (пункт 7)
#   ADMIN_EMAIL/PASSWORD — первый администратор, создаётся при запуске (регистрация даёт только user)
# =====================================================================

import os

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_MINUTES = int(os.environ.get("ACCESS_TOKEN_MINUTES", "30"))

CORS_ORIGINS = [origin.strip() for origin in os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",")]

LOGIN_RATE_LIMIT = os.environ.get("LOGIN_RATE_LIMIT", "5/minute")

ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@example.com")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin12345")

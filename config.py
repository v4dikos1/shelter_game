import os

# Токен для Telegram-бота
API_TOKEN = os.getenv("API_TOKEN")

# Параметры подключения к Redis
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))

CONFIG_FILE = os.getenv("CONFIG_FILE", "config.json")

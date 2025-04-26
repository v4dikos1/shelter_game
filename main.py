import asyncio

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage

from commands import lobby_commands
from config import API_TOKEN
from storage import redis_repository

dp = Dispatcher(storage=RedisStorage(redis=redis_repository.redis_client))
dp.include_router(lobby_commands.router)


async def main() -> None:
    bot = Bot(token=API_TOKEN)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from models.error import BadResponse, NOT_FOUND_ERROR
from models.lobby import Lobby
from storage.redis_repository import get_lobby_by_user


async def get_main_menu(user_id: int) -> ReplyKeyboardMarkup | None:
    user_lobby = await get_lobby_by_user(user_id)
    if isinstance(user_lobby, BadResponse) and user_lobby.code == NOT_FOUND_ERROR:
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Создать лобби")],
                [KeyboardButton(text="Присоединиться к лобби")]
            ],
            resize_keyboard=True
        )

    if isinstance(user_lobby, Lobby) and not user_lobby.started:
        player = next((p for p in user_lobby.players if p.user_id == user_id), None)
        is_creator = player.user_id == user_lobby.owner.user_id

        buttons = [
            [KeyboardButton(text="Список игроков")],
            [KeyboardButton(text="Выйти из лобби")]
        ]

        if is_creator:
            buttons.insert(0, [KeyboardButton(text="Начать игру")])

        return ReplyKeyboardMarkup(
            keyboard=buttons,
            resize_keyboard=True
        )

    elif isinstance(user_lobby, Lobby) and user_lobby.started:
        buttons = [
            [KeyboardButton(text="Мой персонаж")],
            [KeyboardButton(text="Бункер")],
            [KeyboardButton(text="Игроки")],
            [KeyboardButton(text="Действия")],
            [KeyboardButton(text="Выйти из игры")],
        ]
        return ReplyKeyboardMarkup(
            keyboard=buttons,
            resize_keyboard=True
        )

    return None

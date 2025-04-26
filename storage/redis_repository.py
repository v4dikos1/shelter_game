import json

import redis.asyncio as redis

from config import REDIS_HOST, REDIS_PORT
from models.error import BadResponse, NOT_FOUND_ERROR, BAD_REQUEST, INTERNAL_ERROR
from models.lobby import Lobby, Player

redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

LOBBY_KEY_PREFIX = "lobby:"
USER_LOBBY_PREFIX = "user_lobby:"

async def get_user_lobby_code(user_id: int) -> str | BadResponse:
    """Получает код лобби, в котором находится пользователь."""
    try:
        raw = await redis_client.get(USER_LOBBY_PREFIX + str(user_id))
        if raw is None:
            return BadResponse("Пользователь не состоит в лобби", NOT_FOUND_ERROR)
        return json.loads(raw)
    except Exception as e:
        return BadResponse(str(e), INTERNAL_ERROR)


async def get_lobby_by_code(code: str) -> Lobby | BadResponse:
    """Получает объект лобби по коду."""
    try:
        raw = await redis_client.get(LOBBY_KEY_PREFIX + code)
        if raw is None:
            return BadResponse("Лобби не найдено", NOT_FOUND_ERROR)
        return Lobby.from_dict(json.loads(raw))
    except Exception as e:
        return BadResponse(str(e), INTERNAL_ERROR)


async def get_lobby_by_user(user_id: int) -> Lobby | BadResponse:
    """Получает объект лобби по ID пользователя."""
    code = await get_user_lobby_code(user_id)
    if isinstance(code, BadResponse):
        return code
    return await get_lobby_by_code(code)


async def add_user_to_lobby(user_id: int, username: str, code: str) -> Lobby | BadResponse:
    lobby = await get_lobby_by_code(code)
    if isinstance(lobby, BadResponse):
        return lobby

    user_lobby = await get_user_lobby_code(user_id)
    if not isinstance(user_lobby, BadResponse):
        return BadResponse("Вы уже находитесь в другом лобби", BAD_REQUEST)
    elif user_lobby == lobby.code:
        return BadResponse("Вы уже присоединились к этому лобби", BAD_REQUEST)

    lobby.players.append(Player(user_id=user_id, username=username, cards=None))

    try:
        await redis_client.set(LOBBY_KEY_PREFIX + lobby.code, json.dumps(lobby.to_dict()))
        await redis_client.set(USER_LOBBY_PREFIX + str(user_id), json.dumps(lobby.code))
    except Exception as e:
        return BadResponse(str(e), INTERNAL_ERROR)

    return lobby


async def create_lobby_and_add_user(owner_id: int, lobby: Lobby) -> Lobby | BadResponse:
    existing_lobby = await get_lobby_by_code(lobby.code)
    if not isinstance(existing_lobby, BadResponse):
        return BadResponse("Лобби с таким кодом уже существует", BAD_REQUEST)

    try:
        await redis_client.set(LOBBY_KEY_PREFIX + lobby.code, json.dumps(lobby.to_dict()))
        await redis_client.set(USER_LOBBY_PREFIX + str(owner_id), json.dumps(lobby.code))
    except Exception as e:
        return BadResponse(str(e), INTERNAL_ERROR)

    return lobby


async def remove_user_from_lobby(user_id: int, code: str) -> Lobby | BadResponse:
    lobby = await get_lobby_by_code(code)
    if isinstance(lobby, BadResponse):
        return lobby

    user_lobby = await get_user_lobby_code(user_id)
    if isinstance(user_lobby, BadResponse):
        return user_lobby

    if user_lobby != lobby.code:
        return BadResponse("Вы находитесь в другом лобби", BAD_REQUEST)

    player_to_remove = next((p for p in lobby.players if p.user_id == user_id), None)
    lobby.players.remove(player_to_remove)

    if lobby.owner.user_id == user_id and len(lobby.players) > 0:
        lobby.owner.user_id = lobby.players[0].user_id

    try:
        if len(lobby.players) == 0:
            await redis_client.delete(LOBBY_KEY_PREFIX + code)
        else:
            await redis_client.set(LOBBY_KEY_PREFIX + lobby.code, json.dumps(lobby.to_dict()))

        await redis_client.delete(USER_LOBBY_PREFIX + str(user_id), json.dumps(lobby.code))
    except Exception as e:
        return BadResponse(str(e), INTERNAL_ERROR)

    return lobby


async def update_lobby_info(lobby: Lobby) -> Lobby | BadResponse:
    try:
        await redis_client.set(LOBBY_KEY_PREFIX + lobby.code, json.dumps(lobby.to_dict()))
        return lobby
    except Exception as e:
        return BadResponse(str(e), INTERNAL_ERROR)
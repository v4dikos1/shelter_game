import random
import secrets
from typing import Dict, List

from aiogram import Bot
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.markdown import bold

from commands.menu_commands import get_main_menu
from models.lobby import Bunker
from models.player_card import PlayerCard
from models.scenario import Item, SpecialCard, BunkerFeature, Scenario
from storage.redis_repository import *
from utils.escape import escape_md
from utils.scenario_loader import SCENARIOS


class JoinLobbyState(StatesGroup):
    waiting_for_code = State()

class RevealCardState(StatesGroup):
    choosing_characteristic = State()

class ActionsState(StatesGroup):
    choosing_action = State()

def generate_lobby_code() -> str:
    return secrets.token_hex(3)


async def create_lobby(owner_id: int, username: str) -> str:
    lobby = Lobby(code=generate_lobby_code(),
                  owner=Player(user_id=owner_id,
                               username=username,
                               cards=None),
                  players=[Player(user_id=owner_id,
                                  username=username,
                                  cards=None)],
                  bunker=None)
    response = await create_lobby_and_add_user(owner_id, lobby)
    if isinstance(response, Lobby):
        return f"Лобби создано!\nКод: ||{response.code}||\nПоделись этим кодом с друзьями"
    else:
        return response.message


async def join_lobby(user_id: int, username: str, code: str, bot: Bot) -> str:
    response = await add_user_to_lobby(user_id, username, code)
    if isinstance(response, Lobby):
        for player in response.players:
            if player.user_id != user_id:
                await send_notification(player.user_id, bot, f"{username} присоединился к лобби")
        return f"Вы присоединились к лобби {response.code}"
    return response.message


async def leave_lobby(user_id: int, username: str, bot: Bot) -> str:
    user_lobby = await get_user_lobby_code(user_id)
    if isinstance(user_lobby, BadResponse):
        return user_lobby.message

    response = await remove_user_from_lobby(user_id, user_lobby)
    if isinstance(response, Lobby):
        for player in response.players:
            if player.user_id != user_id:
                await send_notification(player.user_id, bot, f"{username} вышел из лобби")
        return f"Вы покинули лобби"
    else:
        return response.message


async def get_lobby_info(user_id: int) -> str:
    response = await get_lobby_by_user(user_id)

    if isinstance(response, Lobby):
        players_output = []

        for player in response.players:
            card = player.cards
            card_parts = []

            if card:
                if card.characteristics:
                    characteristics = "\n".join([
                        f"• {escape_md(k)}: {escape_md(v) if k in card.revealed_values else 'неизвестно'}"
                        for k, v in card.characteristics.items()
                    ])
                    card_parts.append(f"{bold('Характеристики')}:\n{characteristics}")

                if card.items:
                    items = "\n".join([
                        f"• {escape_md(item.name) if item.name in card.revealed_values else 'неизвестно'}"
                        for item in card.items
                    ])
                    card_parts.append(f"{bold('Предметы')}:\n{items}")

                if card.special_cards:
                    specials = "\n".join([
                        f"• {escape_md(s.name) if s.name in card.revealed_values else 'неизвестно'}"
                        for s in card.special_cards
                    ])
                    card_parts.append(f"{bold('Спец. карты')}:\n{specials}")

            if card_parts:
                player_info = f"\n\n📌 {bold(player.username)}\n" + "\n".join(card_parts)
            else:
                player_info = f"\n📌 {bold(player.username)}"

            players_output.append(player_info)

        lobby_header = f"🏠 Лобби: ||{escape_md(response.code)}||\n👑 Владелец: {escape_md(response.owner.username)}"
        return f"{lobby_header}\n\n{bold('Игроки')}:" + "".join(players_output)

    return escape_md(response.message)


async def start_game(owner_id: int, bot: Bot) -> str:
    lobby = await get_lobby_by_user(owner_id)
    if isinstance(lobby, BadResponse):
        return lobby.message

    if lobby.owner.user_id != owner_id:
        return "Только владелец лобби может начать игру"

    lobby.started = True
    response = await update_lobby_info(lobby)
    if isinstance(response, BadResponse):
        return "Ошибка. Попробуйте позже"

    for player in lobby.players:
        if player.user_id != lobby.owner.user_id:
            await send_notification(player.user_id, bot, f"Игра началась!")

    scenario = random.choice(SCENARIOS)
    await update_lobby_info(assign_cards(response, scenario))

    return f"Игра началась!"


def assign_cards(lobby: Lobby, scenario: Scenario) -> Lobby | BadResponse:
    lobby.bunker = Bunker(
        scenario_id=scenario.id,
        scenario_name=scenario.name,
        scenario_description=scenario.description,
        features=[BunkerFeature(name=bf.name, description=bf.description) for bf in scenario.bunker_features]
    )

    for player in lobby.players:
        characteristics = generate_characteristics(scenario.characteristics)

        items = generate_items(scenario.items)

        special_cards = generate_special_cards(scenario.special_cards)

        player.cards = PlayerCard(
            characteristics=characteristics,
            items=items,
            special_cards=special_cards
        )

    return lobby

def generate_characteristics(characteristics: Dict[str, List[str]]) -> Dict[str, str]:
    generated_characteristics = {}
    for characteristic, values in characteristics.items():
        generated_characteristics[characteristic] = random.choice(values)
    return generated_characteristics

def generate_items(items: List[Item]) -> List[Item]:
    return items

def generate_special_cards(special_cards: List[SpecialCard]) -> List[SpecialCard]:
    return special_cards

async def get_bunker_info(user_id: int, bot: Bot) -> str | BadResponse:
    response = await get_lobby_by_user(user_id)
    if isinstance(response, BadResponse):
        return response

    bunker = response.bunker

    features_text = ""
    if bunker.features:
        features_text = "\n\n" + bold("Особенности бункера") + ":\n" + "\n".join(
            [f"• {escape_md(feature.name)}: {escape_md(feature.description)}" for feature in bunker.features]
        )

    return (
        f"🏰 {bold('Бункер')}\n\n"
        f"{bold('Сценарий')}: {escape_md(bunker.scenario_name)}\n\n"
        f"{bunker.scenario_description}"
        f"{features_text}"
    )

async def get_player_info(user_id: int) -> str:
    response = await get_lobby_by_user(user_id)

    if isinstance(response, Lobby):
        player = next((p for p in response.players if p.user_id == user_id), None)
        if not player:
            return "❗ Вы не найдены в этом лобби."

        card = player.cards
        card_parts = []

        if card:
            if card.characteristics:
                characteristics = "\n".join([
                    f"• {escape_md(k)}: {escape_md(v)}"
                    for k, v in card.characteristics.items()
                ])
                card_parts.append(f"{bold('Характеристики')}:\n{characteristics}")

            if card.items:
                items = "\n".join([
                    f"• {escape_md(item.name)}"
                    for item in card.items
                ])
                card_parts.append(f"{bold('Предметы')}:\n{items}")

            if card.special_cards:
                specials = "\n".join([
                    f"• {escape_md(s.name)}"
                    for s in card.special_cards
                ])
                card_parts.append(f"{bold('Спец. карты')}:\n{specials}")

        player_info = bold(player.username)
        if card_parts:
            player_info += "\n" + "\n\n".join(card_parts)

        return player_info

    return escape_md(response.message)


async def get_player_card(user_id: int) -> PlayerCard | BadResponse:
    lobby = await get_lobby_by_user(user_id)

    if isinstance(lobby, Lobby):
        player = next((p for p in lobby.players if p.user_id == user_id), None)
        if player:
            return player.cards
        else:
            return BadResponse("Игрок не найден", NOT_FOUND_ERROR)

    return lobby

async def reveal_player_value(user_id: int, value_name: str, bot: Bot) -> bool:
    lobby = await get_lobby_by_user(user_id)

    if isinstance(lobby, Lobby):
        player = next((p for p in lobby.players if p.user_id == user_id), None)
        if player and player.cards:
            if value_name not in player.cards.revealed_values:
                player.cards.revealed_values.append(value_name)
                await update_lobby_info(lobby)

                for lobby_player in lobby.players:
                    if lobby_player.user_id != user_id:
                        await send_notification(lobby_player.user_id, bot, f"{player.username} раскрыл {value_name}")

                return True

    return False

async def send_notification(user_id: int, bot: Bot, message: str) -> None | BadResponse:
    try:
        menu = await get_main_menu(user_id)
        await bot.send_message(user_id, message, reply_markup=menu)
        return None
    except Exception as e:
        print(f"Не удалось отправить сообщение пользователю {user_id}: {e}")
        return BadResponse("Возникла непредвиденная ошибка", INTERNAL_ERROR)

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

from services.lobby_service import *
from utils.escape import escape_md

router = Router()

@router.message(Command('start'))
async def cmd_start(message: Message):
    menu = await get_main_menu(message.from_user.id)
    await message.answer(escape_md(f"Привет, {message.from_user.username}. Начнем играть?"), reply_markup=menu, parse_mode="MarkdownV2")

@router.message(Command("create"))
async def handle_create(message: Message):
    response = await create_lobby(owner_id=message.from_user.id, username=message.from_user.username)
    menu = await get_main_menu(message.from_user.id)
    await message.answer(escape_md(response), reply_markup=menu, parse_mode="MarkdownV2")

@router.message(Command("join"))
async def handle_join(message: Message, command: Command, bot: Bot):
    if not command.args:
        await message.answer(escape_md("Пожалуйста, укажи код лобби: /join <код>"))
        return

    code = command.args.strip()
    result = await join_lobby(
        user_id=message.from_user.id,
        username=message.from_user.username or message.from_user.full_name,
        code=code,
        bot=bot
    )
    menu = await get_main_menu(message.from_user.id)
    await message.answer(escape_md(result), reply_markup=menu, parse_mode="MarkdownV2")

@router.message(Command('leave'))
async def cmd_leave(message: Message, bot: Bot):
    response = await leave_lobby(message.from_user.id, message.from_user.username, bot)
    menu = await get_main_menu(message.from_user.id)
    await message.answer(escape_md(response), reply_markup=menu, parse_mode="MarkdownV2")

@router.message(Command('lobby'))
async def cmd_lobby(message: Message):
    response = await get_lobby_info(message.from_user.id)
    await message.answer(escape_md(response), parse_mode="MarkdownV2")

@router.message(Command('me'))
async def cmd_me(message: Message):
    response = await get_player_info(message.from_user.id)
    await message.answer(escape_md(response), parse_mode="MarkdownV2")

@router.message(Command('start_game'))
async def cmd_start_game(message: Message, bot: Bot):
    response = await start_game(message.from_user.id, bot=bot)
    menu = await get_main_menu(message.from_user.id)
    await message.answer(escape_md(response), parse_mode="MarkdownV2", reply_markup=menu)

@router.message(Command("menu"))
async def show_menu(message: Message):
    keyboard = await get_main_menu(message.from_user.id)
    await message.answer("Меню действий:", reply_markup=keyboard, parse_mode="MarkdownV2")

@router.message(F.text == "Создать лобби")
async def on_create_lobby_click(message: Message):
    await handle_create(message)

@router.message(F.text == "Присоединиться к лобби")
async def on_join_lobby_click(message: Message,  state: FSMContext):
    await message.answer("Введи код лобби", parse_mode="MarkdownV2")
    await state.set_state(JoinLobbyState.waiting_for_code)

@router.message(JoinLobbyState.waiting_for_code)
async def on_lobby_code_received(message: Message, state: FSMContext, bot: Bot):
    code = message.text.strip()
    result = await join_lobby(
        user_id=message.from_user.id,
        username=message.from_user.username or message.from_user.full_name,
        code=code,
        bot=bot
    )
    await state.clear()

    menu = await get_main_menu(message.from_user.id)
    await message.answer(result, reply_markup=menu, parse_mode="MarkdownV2")

@router.message(Command("bunker"))
async def handle_bunker_click(message: Message, bot: Bot):
    response = await get_bunker_info(message.from_user.id, bot)
    menu = await get_main_menu(message.from_user.id)
    await message.answer(response, reply_markup=menu)


@router.message(F.text == "Действия")
async def on_actions_click(message: Message, state: FSMContext):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Раскрыть карту")],
            [KeyboardButton(text="Назад")],
        ],
        resize_keyboard=True
    )
    await state.set_state(ActionsState.choosing_action)
    await message.answer("Что вы хотите сделать?", reply_markup=keyboard)


@router.message(ActionsState.choosing_action)
async def on_action_chosen(message: Message, state: FSMContext):
    text = message.text.strip()

    if text == "Назад":
        keyboard = await get_main_menu(message.from_user.id)
        await state.clear()
        await message.answer("Что вы хотите сделать?", reply_markup=keyboard)
        return

    if text == "Раскрыть карту":
        player_card = await get_player_card(message.from_user.id)
        characteristics = list(player_card.characteristics.keys()) + \
                          [item.name for item in player_card.items] + \
                          [special_card.name for special_card in player_card.special_cards]

        unrevealed_characteristics = [name for name in characteristics if name not in player_card.revealed_values]

        if not unrevealed_characteristics:
            await message.answer("Все характеристики уже раскрыты!")
            return

        rows = []
        for i in range(0, len(unrevealed_characteristics), 2):
            row = []
            for j in range(i, min(i + 2, len(unrevealed_characteristics))):  # по две кнопки на ряд
                row.append(KeyboardButton(text=unrevealed_characteristics[j]))
            rows.append(row)

        rows.append([KeyboardButton(text="Назад")])

        keyboard = ReplyKeyboardMarkup(
            keyboard=rows,
            resize_keyboard=True
        )

        await state.set_state(RevealCardState.choosing_characteristic)
        await message.answer("Какую характеристику вы хотите раскрыть?", reply_markup=keyboard)
        return

    await message.answer("Пожалуйста, выбери действие через кнопки")


@router.message(RevealCardState.choosing_characteristic)
async def on_characteristic_chosen(message: Message, state: FSMContext, bot: Bot):
    text = message.text.strip()

    if text == "Назад":
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Раскрыть карту")],
                [KeyboardButton(text="Назад")],
            ],
            resize_keyboard=True
        )
        await state.set_state(ActionsState.choosing_action)
        await message.answer("Что вы хотите сделать?", reply_markup=keyboard)
        return

    characteristic_name = text
    await reveal_player_value(message.from_user.id, characteristic_name, bot)
    await state.clear()

    menu = await get_main_menu(message.from_user.id)
    await message.answer(f"Вы успешно раскрыли: {characteristic_name}", reply_markup=menu, parse_mode="MarkdownV2")


@router.message(F.text == "Начать игру")
async def on_start_game_click(message: Message, bot: Bot):
    await cmd_start_game(message, bot)

@router.message(F.text == "Список игроков")
async def on_lobby_info_click(message: Message):
    await cmd_lobby(message)

@router.message(F.text == "Игроки")
async def on_lobby_players_click(message: Message):
    await cmd_lobby(message)

@router.message(F.text == "Выйти из лобби")
async def on_leave_lobby_click(message: Message, bot: Bot):
    await cmd_leave(message, bot)

@router.message(F.text == "Выйти из игры")
async def on_leave_game_click(message: Message, bot: Bot):
    await cmd_leave(message, bot)

@router.message(F.text == "Бункер")
async def on_leave_lobby_click(message: Message, bot: Bot):
    await handle_bunker_click(message, bot)

@router.message(F.text == "Мой персонаж")
async def on_me_click(message: Message):
    await cmd_me(message)

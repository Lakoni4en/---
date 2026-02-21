"""
🎰 Бесконечная гача — Telegram бот
Процедурная генерация предметов, ежедневные тяги, магазин Stars, коллекция
"""
import asyncio
import logging
from datetime import datetime

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    InlineKeyboardMarkup as IKM,
    InlineKeyboardButton as IKB,
    LabeledPrice,
    PreCheckoutQuery,
)
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

import config
import database as db
from gacha_data import (
    RARITY_EMOJI, RARITY_NAMES, THEMES,
    GACHA_PACKS, gacha_pull, generate_daily_quests,
    format_item_short, format_item_full, get_collection_stats,
    REFERRAL_BONUS,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=config.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()


# ======== КЛАВИАТУРЫ ========
def kb_main():
    return IKM(inline_keyboard=[
        [IKB(text="🎰 Тянуть гача", callback_data="pull")],
        [IKB(text="📦 Коллекция", callback_data="collection"),
         IKB(text="📜 Квесты", callback_data="quests")],
        [IKB(text="👤 Профиль", callback_data="profile"),
         IKB(text="🏆 Топ", callback_data="top")],
        [IKB(text="🎁 Рефералка", callback_data="referral"),
         IKB(text="🏪 Магазин", callback_data="shop")],
    ])


def kb_back():
    return IKM(inline_keyboard=[[IKB(text="🏠 Меню", callback_data="menu")]])


# ======== /START ========
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or ""
    first_name = message.from_user.first_name or "Игрок"
    
    # Проверяем реферальную ссылку
    referrer_id = None
    args = message.text.split()
    if len(args) > 1 and args[1].startswith("ref"):
        try:
            referrer_id = int(args[1][3:])
            if referrer_id != user_id:
                # Начисляем бонусы
                await db.add_stars(referrer_id, config.REFERRAL_BONUS_REFERRER_STARS)
                await db.add_gold(referrer_id, config.REFERRAL_BONUS_REFERRER_GOLD)
                await db.add_stars(user_id, config.REFERRAL_BONUS_REFEREE_STARS)
                await db.add_gold(user_id, config.REFERRAL_BONUS_REFEREE_GOLD)
                
                try:
                    await bot.send_message(
                        referrer_id,
                        f"🎉 По твоей ссылке пришёл новый игрок!\n"
                        f"💎 +{config.REFERRAL_BONUS_REFERRER_STARS} Stars\n"
                        f"💰 +{config.REFERRAL_BONUS_REFERRER_GOLD} золота"
                    )
                except:
                    pass
        except:
            pass
    
    # Создаём игрока
    await db.create_player(user_id, username, first_name, referrer_id)
    
    # Ежедневный бонус
    daily = await db.check_daily(user_id)
    daily_text = ""
    if daily:
        ds = daily["daily_streak"]
        bonus_gold = config.DAILY_BONUS_GOLD + (ds * 50)
        bonus_stars = config.DAILY_BONUS_STARS + (1 if ds >= 7 else 0)
        await db.add_gold(user_id, bonus_gold)
        await db.add_stars(user_id, bonus_stars)
        daily_text = (
            f"\n🌅 <b>Ежедневный бонус!</b>\n"
            f"💰 +{bonus_gold} золота  💎 +{bonus_stars} Stars\n"
            f"📅 Дней подряд: {ds}\n"
        )
    
    # Создаём квесты если их нет
    quests = await db.get_daily_quests(user_id)
    if not quests:
        ql = generate_daily_quests(3)
        await db.create_daily_quests(user_id, ql)
    
    player = await db.get_player(user_id)
    free_left = await db.get_free_pulls_left(user_id)
    collection_count = await db.get_collection_count(user_id)
    
    text = (
        f"🎰 <b>Добро пожаловать в Бесконечную гача!</b>\n\n"
        f"👋 Привет, <b>{first_name}</b>!\n\n"
        f"💰 Золото: {player['gold']}\n"
        f"💎 Stars: {player['stars']}\n"
        f"📦 Коллекция: {collection_count} предметов\n"
        f"🎰 Бесплатных тягов: {free_left}/{config.DAILY_FREE_PULLS}\n"
        f"{daily_text}\n"
        f"<i>Каждый предмет уникален и генерируется процедурно!</i>\n"
        f"<i>Коллекция никогда не заканчивается! 🚀</i>"
    )
    
    await message.answer(text, reply_markup=kb_main())


@dp.callback_query(F.data == "menu")
async def cb_menu(callback: types.CallbackQuery):
    await callback.answer()
    player = await db.get_player(callback.from_user.id)
    if not player:
        return
    
    free_left = await db.get_free_pulls_left(callback.from_user.id)
    collection_count = await db.get_collection_count(callback.from_user.id)
    
    text = (
        f"🎰 <b>Бесконечная гача</b>\n\n"
        f"💰 {player['gold']}  💎 {player['stars']}\n"
        f"📦 {collection_count} предметов\n"
        f"🎰 {free_left}/{config.DAILY_FREE_PULLS} бесплатных\n\n"
        f"Выбери действие:"
    )
    
    try:
        await callback.message.edit_text(text, reply_markup=kb_main())
    except:
        await callback.message.answer(text, reply_markup=kb_main())


# ======== ГАЧА ========
@dp.callback_query(F.data == "pull")
async def cb_pull(callback: types.CallbackQuery):
    await callback.answer()
    player = await db.get_player(callback.from_user.id)
    if not player:
        return
    
    free_left = await db.get_free_pulls_left(callback.from_user.id)
    
    buttons = []
    
    # Бесплатные тяги
    if free_left > 0:
        buttons.append([IKB(
            text=f"🪙 Бесплатный тяг ({free_left} осталось)",
            callback_data="pull_free"
        )])
    
    # Платные пакеты
    for pack_id, pack in GACHA_PACKS.items():
        if pack_id == "single_free":
            continue
        cost_text = f"{pack['cost_stars']}⭐" if pack['cost_stars'] > 0 else f"{pack['cost_gold']}💰"
        buttons.append([IKB(
            text=f"{pack['name']} — {cost_text}",
            callback_data=f"pull_{pack_id}"
        )])
    
    buttons.append([IKB(text="🏠 Меню", callback_data="menu")])
    
    text = (
        f"🎰 <b>Тянуть гача</b>\n\n"
        f"💰 Золото: {player['gold']}\n"
        f"💎 Stars: {player['stars']}\n\n"
        f"<b>Доступные пакеты:</b>\n"
        f"🪙 Бесплатно — {free_left}/{config.DAILY_FREE_PULLS} в день\n"
        f"💎 Премиум — лучшие шансы на редкие предметы\n"
        f"📦 Пакеты — выгоднее и с гарантиями!\n\n"
        f"<i>Каждый предмет уникален!</i>"
    )
    
    try:
        await callback.message.edit_text(text, reply_markup=IKM(inline_keyboard=buttons))
    except:
        await callback.message.answer(text, reply_markup=IKM(inline_keyboard=buttons))


@dp.callback_query(F.data == "pull_free")
async def cb_pull_free(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    free_left = await db.get_free_pulls_left(user_id)
    
    if free_left <= 0:
        await callback.answer("Бесплатные тяги закончились! Завтра будет больше.", show_alert=True)
        return
    
    await callback.answer()
    await db.use_free_pull(user_id)
    
    # Тяга
    items = gacha_pull("single_free")
    item = items[0]
    
    # Добавляем в коллекцию
    await db.add_to_collection(user_id, item)
    
    # Обновляем квесты
    await db.update_quest_progress(user_id, "daily_pull")
    
    # Проверяем редкость для квестов
    if item["rarity"] == "rare":
        await db.update_quest_progress(user_id, "collect_rare")
    elif item["rarity"] == "epic":
        await db.update_quest_progress(user_id, "collect_epic")
    elif item["rarity"] in ("legendary", "mythic"):
        await db.update_quest_progress(user_id, "collect_legendary")
    
    text = (
        f"🎰 <b>Бесплатный тяг!</b>\n\n"
        f"{format_item_full(item)}\n\n"
        f"✅ Добавлено в коллекцию!\n"
        f"🎰 Осталось: {free_left - 1}/{config.DAILY_FREE_PULLS}"
    )
    
    keyboard = IKM(inline_keyboard=[
        [IKB(text="🎰 Ещё тяг", callback_data="pull")],
        [IKB(text="📦 Коллекция", callback_data="collection")],
        [IKB(text="🏠 Меню", callback_data="menu")],
    ])
    
    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except:
        await callback.message.answer(text, reply_markup=keyboard)


@dp.callback_query(F.data.startswith("pull_"))
async def cb_pull_pack(callback: types.CallbackQuery):
    pack_id = callback.data.replace("pull_", "")
    
    if pack_id not in GACHA_PACKS:
        await callback.answer("Ошибка!", show_alert=True)
        return
    
    pack = GACHA_PACKS[pack_id]
    user_id = callback.from_user.id
    
    # Проверка оплаты
    if pack["cost_stars"] > 0:
        if not await db.spend_stars(user_id, pack["cost_stars"]):
            await callback.answer(f"Не хватает Stars! Нужно {pack['cost_stars']}⭐", show_alert=True)
            return
    elif pack["cost_gold"] > 0:
        if not await db.spend_gold(user_id, pack["cost_gold"]):
            await callback.answer(f"Не хватает золота! Нужно {pack['cost_gold']}💰", show_alert=True)
            return
    
    await callback.answer()
    
    # Тяги
    items = gacha_pull(pack_id)
    await db.use_premium_pull(user_id, len(items))
    
    # Добавляем в коллекцию
    for item in items:
        await db.add_to_collection(user_id, item)
    
    # Обновляем квесты
    await db.update_quest_progress(user_id, "daily_pull", len(items))
    
    # Проверяем редкости
    for item in items:
        if item["rarity"] == "rare":
            await db.update_quest_progress(user_id, "collect_rare")
        elif item["rarity"] == "epic":
            await db.update_quest_progress(user_id, "collect_epic")
        elif item["rarity"] in ("legendary", "mythic"):
            await db.update_quest_progress(user_id, "collect_legendary")
    
    # Форматируем результат
    if len(items) == 1:
        text = f"🎰 <b>{pack['name']}</b>\n\n{format_item_full(items[0])}\n\n✅ Добавлено в коллекцию!"
    else:
        lines = [f"🎰 <b>{pack['name']}</b>\n\n<b>Получено {len(items)} предметов:</b>\n"]
        for item in items:
            lines.append(f"{format_item_short(item)}")
        text = "\n".join(lines) + "\n\n✅ Все добавлены в коллекцию!"
    
    # Обновляем размер коллекции для квеста
    collection_count = await db.get_collection_count(user_id)
    if collection_count >= 10:
        await db.update_quest_progress(user_id, "collection_size", 0)  # Проверка
    if collection_count >= 50:
        await db.update_quest_progress(user_id, "collection_size", 0)
    
    keyboard = IKM(inline_keyboard=[
        [IKB(text="🎰 Ещё тяг", callback_data="pull")],
        [IKB(text="📦 Коллекция", callback_data="collection")],
        [IKB(text="🏠 Меню", callback_data="menu")],
    ])
    
    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except:
        await callback.message.answer(text, reply_markup=keyboard)


# ======== КОЛЛЕКЦИЯ ========
@dp.callback_query(F.data == "collection")
async def cb_collection(callback: types.CallbackQuery):
    await callback.answer()
    await show_collection(callback.from_user.id, callback.message)


@dp.callback_query(F.data.startswith("colp_"))
async def cb_collection_page(callback: types.CallbackQuery):
    await callback.answer()
    page = int(callback.data.replace("colp_", ""))
    await show_collection(callback.from_user.id, callback.message, page=page)


async def show_collection(user_id: int, message: types.Message, page: int = 1):
    collection = await db.get_collection(user_id)
    
    if not collection:
        text = "📦 <b>Коллекция пуста!</b>\n\nСделай свой первый тяг! 🎰"
        try:
            await message.edit_text(text, reply_markup=IKM(inline_keyboard=[
                [IKB(text="🎰 Тянуть гача", callback_data="pull")],
                [IKB(text="🏠 Меню", callback_data="menu")],
            ]))
        except:
            await message.answer(text, reply_markup=kb_back())
        return
    
    # Статистика
    stats = get_collection_stats(collection)
    
    # Пагинация
    per_page = 5
    total_pages = max(1, (len(collection) + per_page - 1) // per_page)
    page = max(1, min(page, total_pages))
    start = (page - 1) * per_page
    page_items = collection[start:start + per_page]
    
    lines = [
        f"📦 <b>Коллекция</b> ({len(collection)} предметов)\n",
        f"📊 <b>Статистика:</b>",
        f"💪 Сила: {stats['total_power']}",
        f"🍀 Удача: {stats['total_luck']:.1f}",
        f"✨ Магия: {stats['total_magic']}\n",
    ]
    
    # По редкости
    lines.append("<b>По редкости:</b>")
    for rarity in ["common", "uncommon", "rare", "epic", "legendary", "mythic"]:
        count = stats["by_rarity"].get(rarity, 0)
        if count > 0:
            lines.append(f"  {RARITY_EMOJI[rarity]} {RARITY_NAMES[rarity]}: {count}")
    
    lines.append("\n<b>Последние предметы:</b>")
    for item in page_items:
        lines.append(f"\n{format_item_short(item)}")
    
    text = "\n".join(lines)
    
    # Кнопки
    buttons = []
    for item in page_items:
        buttons.append([IKB(
            text=f"👆 {item['name']}",
            callback_data=f"item_{item['id']}"
        )])
    
    # Навигация
    nav = []
    if page > 1:
        nav.append(IKB(text="◀️", callback_data=f"colp_{page - 1}"))
    if total_pages > 1:
        nav.append(IKB(text=f"{page}/{total_pages}", callback_data="noop"))
    if page < total_pages:
        nav.append(IKB(text="▶️", callback_data=f"colp_{page + 1}"))
    if nav:
        buttons.append(nav)
    
    buttons.append([IKB(text="🏠 Меню", callback_data="menu")])
    
    try:
        await message.edit_text(text, reply_markup=IKM(inline_keyboard=buttons))
    except:
        await message.answer(text, reply_markup=IKM(inline_keyboard=buttons))


@dp.callback_query(F.data.startswith("item_"))
async def cb_item_detail(callback: types.CallbackQuery):
    item_id = int(callback.data.replace("item_", ""))
    collection = await db.get_collection(callback.from_user.id)
    item = next((i for i in collection if i["id"] == item_id), None)
    
    if not item:
        await callback.answer("Предмет не найден!", show_alert=True)
        return
    
    await callback.answer()
    
    text = format_item_full(item)
    
    keyboard = IKM(inline_keyboard=[
        [IKB(text="📦 Коллекция", callback_data="collection")],
        [IKB(text="🏠 Меню", callback_data="menu")],
    ])
    
    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except:
        await callback.message.answer(text, reply_markup=keyboard)


# ======== КВЕСТЫ ========
@dp.callback_query(F.data == "quests")
async def cb_quests(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    
    # Создаём квесты если их нет
    quests = await db.get_daily_quests(user_id)
    if not quests:
        ql = generate_daily_quests(3)
        await db.create_daily_quests(user_id, ql)
        quests = await db.get_daily_quests(user_id)
    
    lines = ["📜 <b>Ежедневные квесты</b>\n"]
    buttons = []
    
    for q in quests:
        status = "✅" if q["is_claimed"] else ("🟢" if q["is_completed"] else "⬜")
        lines.append(f"{status} {q['description']} [{q['progress']}/{q['target']}]")
        lines.append(f"   💰{q['reward_gold']} 💎{q['reward_stars']}⭐")
        
        if q["is_completed"] and not q["is_claimed"]:
            buttons.append([IKB(
                text=f"🎁 Забрать: {q['description']}",
                callback_data=f"qcl_{q['id']}"
            )])
    
    buttons.append([IKB(text="🏠 Меню", callback_data="menu")])
    
    try:
        await callback.message.edit_text("\n".join(lines), reply_markup=IKM(inline_keyboard=buttons))
    except:
        await callback.message.answer("\n".join(lines), reply_markup=IKM(inline_keyboard=buttons))


@dp.callback_query(F.data.startswith("qcl_"))
async def cb_quest_claim(callback: types.CallbackQuery):
    quest_id = int(callback.data.replace("qcl_", ""))
    q = await db.claim_quest(callback.from_user.id, quest_id)
    
    if not q:
        await callback.answer("Уже забрано или не выполнено!", show_alert=True)
        return
    
    await callback.answer(
        f"🎁 +{q['reward_gold']}💰 +{q['reward_stars']}⭐",
        show_alert=True
    )
    
    # Обновляем список
    await cb_quests(callback)


# ======== ПРОФИЛЬ ========
@dp.callback_query(F.data == "profile")
@dp.message(Command("profile"))
async def cb_profile(event: types.CallbackQuery | types.Message):
    if isinstance(event, types.CallbackQuery):
        await event.answer()
        user_id = event.from_user.id
        msg = event.message
        edit = True
    else:
        user_id = event.from_user.id
        msg = event
        edit = False
    
    player = await db.get_player(user_id)
    if not player:
        return
    
    collection_count = await db.get_collection_count(user_id)
    free_left = await db.get_free_pulls_left(user_id)
    referrals = await db.get_referrals_count(user_id)
    
    text = (
        f"👤 <b>Профиль</b>\n\n"
        f"🆔 ID: <code>{user_id}</code>\n"
        f"📅 В игре с: {player['joined_at'][:10] if player['joined_at'] else '—'}\n\n"
        f"💰 Золото: {player['gold']}\n"
        f"💎 Stars: {player['stars']}\n\n"
        f"📦 Коллекция: {collection_count} предметов\n"
        f"🎰 Всего тягов: {player['total_pulls']}\n"
        f"🎰 Бесплатных сегодня: {free_left}/{config.DAILY_FREE_PULLS}\n\n"
        f"👥 Приглашено друзей: {referrals}\n"
        f"📅 Дней подряд: {player['daily_streak']}"
    )
    
    keyboard = IKM(inline_keyboard=[
        [IKB(text="📦 Коллекция", callback_data="collection")],
        [IKB(text="🏠 Меню", callback_data="menu")],
    ])
    
    if edit:
        try:
            await msg.edit_text(text, reply_markup=keyboard)
        except:
            await msg.answer(text, reply_markup=keyboard)
    else:
        await msg.answer(text, reply_markup=keyboard)


# ======== ТОП ========
@dp.callback_query(F.data == "top")
async def cb_top(callback: types.CallbackQuery):
    await callback.answer()
    leaders = await db.get_leaderboard(10)
    rank = await db.get_player_rank(callback.from_user.id)
    
    medals = ["🥇", "🥈", "🥉"]
    lines = []
    
    for i, p in enumerate(leaders):
        medal = medals[i] if i < 3 else f"#{i + 1}"
        name = p["first_name"] or p["username"] or "???"
        lines.append(
            f"{medal} <b>{name}</b> — {p['collection_size']} предметов "
            f"({p['total_pulls']} тягов)"
        )
    
    text = "🏆 <b>Топ коллекционеров</b>\n\n" + "\n".join(lines) if lines else "Пока пусто..."
    text += f"\n\n👤 Твоя позиция: #{rank}"
    
    keyboard = IKM(inline_keyboard=[
        [IKB(text="🏠 Меню", callback_data="menu")],
    ])
    
    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except:
        await callback.message.answer(text, reply_markup=keyboard)


# ======== РЕФЕРАЛКА ========
@dp.callback_query(F.data == "referral")
async def cb_referral(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    referrals = await db.get_referrals_count(user_id)
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref{user_id}"
    
    text = (
        f"🎁 <b>Реферальная система</b>\n\n"
        f"Приглашай друзей и получай бонусы!\n\n"
        f"👥 Приглашено: {referrals}\n\n"
        f"<b>За каждого друга:</b>\n"
        f"• Ты получаешь: 💎{config.REFERRAL_BONUS_REFERRER_STARS}⭐ + 💰{config.REFERRAL_BONUS_REFERRER_GOLD}\n"
        f"• Друг получает: 💎{config.REFERRAL_BONUS_REFEREE_STARS}⭐ + 💰{config.REFERRAL_BONUS_REFEREE_GOLD}\n\n"
        f"🔗 <b>Твоя ссылка:</b>\n"
        f"<code>{ref_link}</code>"
    )
    
    keyboard = IKM(inline_keyboard=[
        [IKB(
            text="📤 Поделиться",
            url=f"https://t.me/share/url?url={ref_link}&text=🎰 Попробуй Бесконечную гача!"
        )],
        [IKB(text="🏠 Меню", callback_data="menu")],
    ])
    
    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except:
        await callback.message.answer(text, reply_markup=keyboard)


# ======== МАГАЗИН ========
@dp.callback_query(F.data == "shop")
async def cb_shop(callback: types.CallbackQuery):
    await callback.answer()
    player = await db.get_player(callback.from_user.id)
    if not player:
        return
    
    text = (
        f"🏪 <b>Магазин Stars</b>\n\n"
        f"💰 Золото: {player['gold']}\n"
        f"💎 Stars: {player['stars']}\n\n"
        f"<b>Купить Stars:</b>\n"
        f"💎 50 Stars — 25 ⭐\n"
        f"💎 150 Stars — 65 ⭐ <i>(+15 бонус)</i>\n"
        f"💎 500 Stars — 200 ⭐ <i>(+75 бонус)</i>\n"
    )
    
    buttons = [
        [IKB(text="💎 50 Stars (25 ⭐)", callback_data="buy_s50")],
        [IKB(text="💎 150 Stars (65 ⭐)", callback_data="buy_s150")],
        [IKB(text="💎 500 Stars (200 ⭐)", callback_data="buy_s500")],
        [IKB(text="🏠 Меню", callback_data="menu")],
    ]
    
    try:
        await callback.message.edit_text(text, reply_markup=IKM(inline_keyboard=buttons))
    except:
        await callback.message.answer(text, reply_markup=IKM(inline_keyboard=buttons))


@dp.callback_query(F.data.startswith("buy_s"))
async def cb_buy_stars(callback: types.CallbackQuery):
    product_id = callback.data.replace("buy_s", "")
    
    shop_items = {
        "50": {"stars": 50, "price": 25, "label": "50 Stars"},
        "150": {"stars": 150, "price": 65, "label": "150 Stars"},
        "500": {"stars": 500, "price": 200, "label": "500 Stars"},
    }
    
    product = shop_items.get(product_id)
    if not product:
        await callback.answer("Ошибка!", show_alert=True)
        return
    
    await callback.answer()
    
    await bot.send_invoice(
        chat_id=callback.from_user.id,
        title=product["label"],
        description="Покупка Stars для гача",
        payload=f"stars_{product_id}_{callback.from_user.id}",
        currency="XTR",
        prices=[LabeledPrice(label=product["label"], amount=product["price"])],
    )


@dp.pre_checkout_query()
async def pre_checkout(pre_checkout: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout.id, ok=True)


@dp.message(F.successful_payment)
async def successful_payment(message: types.Message):
    payload = message.successful_payment.invoice_payload
    parts = payload.split("_")
    
    if "stars" in payload and len(parts) >= 3:
        product_id = parts[1]
        shop_items = {
            "50": 50,
            "150": 150,
            "500": 500,
        }
        stars = shop_items.get(product_id, 0)
        if stars > 0:
            await db.add_stars(message.from_user.id, stars)
            await message.answer(
                f"🎉 <b>Покупка успешна!</b>\n\n"
                f"💎 +{stars} Stars\n\n"
                f"Используй их для премиум тягов! 🎰",
                reply_markup=kb_main()
            )


# ======== ПРОЧЕЕ ========
@dp.callback_query(F.data == "noop")
async def cb_noop(callback: types.CallbackQuery):
    await callback.answer()


@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    text = (
        "📋 <b>Команды:</b>\n\n"
        "/start — Начать игру\n"
        "/profile — Профиль\n"
        "/top — Топ игроков\n"
        "/help — Справка\n\n"
        "<b>🎰 Как играть:</b>\n"
        "• Делай бесплатные тяги каждый день (3/день)\n"
        "• Покупай премиум пакеты за Stars\n"
        "• Собирай уникальную коллекцию\n"
        "• Выполняй ежедневные квесты\n"
        "• Приглашай друзей за бонусы\n\n"
        "<i>Каждый предмет генерируется процедурно и уникален!</i>"
    )
    await message.answer(text, reply_markup=kb_main())


@dp.message(Command("top"))
async def cmd_top(message: types.Message):
    leaders = await db.get_leaderboard(10)
    lines = []
    for i, p in enumerate(leaders):
        medal = ["🥇", "🥈", "🥉"][i] if i < 3 else f"#{i + 1}"
        name = p["first_name"] or "???"
        lines.append(f"{medal} <b>{name}</b> — {p['collection_size']} предметов")
    await message.answer("🏆 <b>Топ</b>\n\n" + "\n".join(lines) if lines else "Пусто", reply_markup=kb_main())


@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    if message.from_user.id != config.ADMIN_ID:
        return
    stats = await db.get_bot_stats()
    await message.answer(
        f"📊 <b>Статистика</b>\n\n"
        f"👥 Игроков: {stats['total_players']}\n"
        f"📦 Предметов: {stats['total_items']}\n"
        f"🎰 Тягов: {stats['total_pulls']}"
    )


@dp.message(F.text)
async def handle_text(message: types.Message):
    player = await db.get_player(message.from_user.id)
    if not player:
        await message.answer("👋 Нажми /start чтобы начать!")
    else:
        await message.answer("🎰 Используй кнопки для игры!", reply_markup=kb_main())


# ======== ЗАПУСК ========
async def main():
    logger.info("🗄 Инициализация БД...")
    await db.init_db()
    logger.info("🎰 Запуск бота 'Бесконечная гача'...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

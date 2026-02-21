"""
🎰 Бесконечная гача — процедурная генерация предметов
Каждый предмет уникален! Бесконечная коллекция.
"""
import random
import hashlib

# ============ РЕДКОСТИ ============
RARITIES = ["common", "uncommon", "rare", "epic", "legendary", "mythic"]

RARITY_EMOJI = {
    "common": "⚪",
    "uncommon": "🟢",
    "rare": "🔵",
    "epic": "🟣",
    "legendary": "🟡",
    "mythic": "💎",
}

RARITY_NAMES = {
    "common": "Обычный",
    "uncommon": "Необычный",
    "rare": "Редкий",
    "epic": "Эпический",
    "legendary": "Легендарный",
    "mythic": "Мифический",
}

RARITY_WEIGHTS_FREE = {
    "common": 50,
    "uncommon": 30,
    "rare": 15,
    "epic": 4,
    "legendary": 1,
    "mythic": 0,
}

RARITY_WEIGHTS_PREMIUM = {
    "common": 0,
    "uncommon": 20,
    "rare": 40,
    "epic": 30,
    "legendary": 9,
    "mythic": 1,
}

# ============ ТЕМЫ (для разнообразия) ============
THEMES = {
    "fantasy": {
        "name": "🧙 Фэнтези",
        "prefixes": ["Магический", "Зачарованный", "Древний", "Священный", "Тёмный", "Светлый", "Эльфийский", "Драконий"],
        "suffixes": ["меч", "посох", "клинок", "щит", "артефакт", "амулет", "кольцо", "книга", "свиток", "кристалл"],
        "descriptions": ["Испускает мягкое свечение", "Покрыт древними рунами", "Хранит силу веков", "Пульсирует магией"],
    },
    "space": {
        "name": "🚀 Космос",
        "prefixes": ["Квантовый", "Звёздный", "Галактический", "Планетарный", "Нейтронный", "Плазменный", "Космический", "Интергалактический"],
        "suffixes": ["бластер", "щит", "двигатель", "сканер", "процессор", "кристалл", "артефакт", "реактор", "телепорт", "зонд"],
        "descriptions": ["Светится неоновым светом", "Испускает радиацию", "Содержит энергию звезды", "Технология будущего"],
    },
    "meme": {
        "name": "😂 Мемы",
        "prefixes": ["Легендарный", "Эпичный", "Мемный", "Вирусный", "Культовый", "Иконичный", "Бессмертный", "Великий"],
        "suffixes": ["мем", "карточка", "артефакт", "реликвия", "легенда", "икона", "шедевр", "классика", "хит", "феномен"],
        "descriptions": ["Вызывает смех", "Легендарный в интернете", "Вирусный контент", "Культовый мем"],
    },
    "crypto": {
        "name": "₿ Крипто",
        "prefixes": ["Блокчейн", "Децентрализованный", "NFT", "Крипто", "Токен", "Майнинг", "Стейкинг", "DeFi"],
        "suffixes": ["токен", "коин", "NFT", "смарт-контракт", "блок", "майнер", "кошелёк", "протокол", "дао", "стейк"],
        "descriptions": ["Хранится в блокчейне", "Децентрализован", "Уникальный токен", "Цифровой актив"],
    },
    "nature": {
        "name": "🌿 Природа",
        "prefixes": ["Лесной", "Цветочный", "Каменный", "Водный", "Огненный", "Ледяной", "Ветреный", "Земной"],
        "suffixes": ["лист", "цветок", "камень", "кристалл", "семя", "корень", "плод", "ветка", "росток", "эссенция"],
        "descriptions": ["Пахнет свежестью", "Пульсирует жизнью", "Связан с природой", "Хранит энергию земли"],
    },
    "tech": {
        "name": "💻 Техно",
        "prefixes": ["Кибер", "Нейро", "Виртуальный", "Цифровой", "ИИ", "Квантовый", "Нано", "Хакерский"],
        "suffixes": ["чип", "процессор", "вирус", "программа", "алгоритм", "данные", "сервер", "интерфейс", "код", "система"],
        "descriptions": ["Светится RGB", "Запускает алгоритмы", "Цифровая реальность", "Искусственный интеллект"],
    },
}

# ============ ПРОЦЕДУРНАЯ ГЕНЕРАЦИЯ ============

def generate_unique_id(seed: str) -> str:
    """Генерирует уникальный ID из seed"""
    return hashlib.md5(seed.encode()).hexdigest()[:12]


def pick_rarity(is_premium: bool = False) -> str:
    """Выбрать редкость по весам"""
    weights = RARITY_WEIGHTS_PREMIUM if is_premium else RARITY_WEIGHTS_FREE
    roll = random.randint(1, 100)
    cumulative = 0
    for rarity, chance in weights.items():
        cumulative += chance
        if roll <= cumulative:
            return rarity
    return "common"


def generate_item_name(theme_id: str, rarity: str) -> tuple[str, str]:
    """Генерирует уникальное название предмета"""
    theme = THEMES[theme_id]
    prefix = random.choice(theme["prefixes"])
    suffix = random.choice(theme["suffixes"])
    name = f"{prefix} {suffix}"
    description = random.choice(theme["descriptions"])
    return name, description


def generate_item_stats(rarity: str) -> dict:
    """Генерирует статы предмета на основе редкости"""
    base_multipliers = {
        "common": 1.0,
        "uncommon": 1.5,
        "rare": 2.5,
        "epic": 4.0,
        "legendary": 7.0,
        "mythic": 12.0,
    }
    mult = base_multipliers.get(rarity, 1.0)
    
    # Рандомные статы с вариацией ±20%
    power = random.uniform(0.8, 1.2) * mult * 10
    luck = random.uniform(0.8, 1.2) * mult * 5
    magic = random.uniform(0.8, 1.2) * mult * 8
    
    return {
        "power": int(power),
        "luck": round(luck, 1),
        "magic": int(magic),
    }


def generate_item(theme_id: str = None, rarity: str = None, is_premium: bool = False) -> dict:
    """
    Генерирует уникальный предмет процедурно.
    Каждый предмет имеет уникальный ID и статы.
    """
    if not theme_id:
        theme_id = random.choice(list(THEMES.keys()))
    
    if not rarity:
        rarity = pick_rarity(is_premium)
    
    # Генерируем уникальный seed
    seed = f"{theme_id}_{rarity}_{random.random()}_{random.randint(1000, 9999)}"
    unique_id = generate_unique_id(seed)
    
    name, description = generate_item_name(theme_id, rarity)
    stats = generate_item_stats(rarity)
    theme = THEMES[theme_id]
    
    # Дополнительные свойства
    special_effects = []
    if rarity in ("legendary", "mythic"):
        effects = ["✨ Светится", "💫 Пульсирует", "🌟 Искрится", "⚡ Энергия", "🔥 Пламя", "❄️ Лёд"]
        special_effects.append(random.choice(effects))
    
    return {
        "unique_id": unique_id,
        "name": name,
        "description": description,
        "rarity": rarity,
        "theme": theme_id,
        "theme_name": theme["name"],
        "power": stats["power"],
        "luck": stats["luck"],
        "magic": stats["magic"],
        "special_effects": special_effects,
        "generated_at": None,  # Заполнится в БД
    }


def generate_item_batch(count: int, is_premium: bool = False, theme_id: str = None) -> list:
    """Генерирует несколько предметов"""
    items = []
    for _ in range(count):
        items.append(generate_item(theme_id=theme_id, is_premium=is_premium))
    return items


# ============ ГАЧА ПАКИ ============
GACHA_PACKS = {
    "single_free": {
        "name": "🪙 Одиночный (бесплатно)",
        "cost_stars": 0,
        "cost_gold": 0,
        "pulls": 1,
        "is_premium": False,
        "daily_limit": 3,
    },
    "single_premium": {
        "name": "💎 Одиночный премиум",
        "cost_stars": 5,
        "cost_gold": 0,
        "pulls": 1,
        "is_premium": True,
    },
    "pack_10": {
        "name": "📦 Пак 10 тягов",
        "cost_stars": 40,
        "cost_gold": 0,
        "pulls": 10,
        "is_premium": True,
        "guarantee": "epic",  # Гарантия хотя бы 1 epic+
    },
    "pack_50": {
        "name": "📦 Пак 50 тягов",
        "cost_stars": 180,
        "cost_gold": 0,
        "pulls": 50,
        "is_premium": True,
        "guarantee": "legendary",  # Гарантия хотя бы 1 legendary+
        "bonus": 5,  # +5 бонусных тягов
    },
    "pack_100": {
        "name": "📦 Мега-пак 100 тягов",
        "cost_stars": 350,
        "cost_gold": 0,
        "pulls": 100,
        "is_premium": True,
        "guarantee": "mythic",  # Гарантия хотя бы 1 mythic
        "bonus": 15,  # +15 бонусных
    },
}


def gacha_pull(pack_id: str) -> list:
    """Выполняет тяги по пакету"""
    pack = GACHA_PACKS[pack_id]
    items = []
    
    for _ in range(pack["pulls"]):
        items.append(generate_item(is_premium=pack.get("is_premium", False)))
    
    # Гарантия (если есть)
    if pack.get("guarantee"):
        guarantee_rarity = pack["guarantee"]
        has_guaranteed = any(i["rarity"] in ("epic", "legendary", "mythic") for i in items)
        if not has_guaranteed:
            # Заменяем последний предмет на гарантированный
            items[-1] = generate_item(rarity=guarantee_rarity, is_premium=True)
    
    # Бонусные тяги
    if pack.get("bonus"):
        for _ in range(pack["bonus"]):
            items.append(generate_item(is_premium=True))
    
    return items


# ============ КВЕСТЫ ============
QUEST_TEMPLATES = [
    {
        "type": "daily_pull",
        "target": 1,
        "description": "Сделай 1 бесплатный тяг",
        "reward_gold": 100,
        "reward_stars": 0,
    },
    {
        "type": "daily_pull",
        "target": 3,
        "description": "Сделай 3 бесплатных тяга",
        "reward_gold": 300,
        "reward_stars": 2,
    },
    {
        "type": "collect_rare",
        "target": 1,
        "description": "Получи 1 редкий предмет",
        "reward_gold": 200,
        "reward_stars": 1,
    },
    {
        "type": "collect_epic",
        "target": 1,
        "description": "Получи 1 эпический предмет",
        "reward_gold": 500,
        "reward_stars": 3,
    },
    {
        "type": "collect_legendary",
        "target": 1,
        "description": "Получи 1 легендарный предмет",
        "reward_gold": 1000,
        "reward_stars": 10,
    },
    {
        "type": "collection_size",
        "target": 10,
        "description": "Собери 10 уникальных предметов",
        "reward_gold": 400,
        "reward_stars": 5,
    },
    {
        "type": "collection_size",
        "target": 50,
        "description": "Собери 50 уникальных предметов",
        "reward_gold": 2000,
        "reward_stars": 20,
    },
    {
        "type": "theme_complete",
        "target": 1,
        "description": "Собери предмет из каждой темы",
        "reward_gold": 800,
        "reward_stars": 8,
    },
]


def generate_daily_quests(count: int = 3) -> list:
    """Генерирует ежедневные квесты"""
    quests = []
    types_used = set()
    shuffled = random.sample(QUEST_TEMPLATES, len(QUEST_TEMPLATES))
    
    for q in shuffled:
        if q["type"] not in types_used and len(quests) < count:
            quests.append(q.copy())
            types_used.add(q["type"])
    
    while len(quests) < count:
        quests.append(random.choice(QUEST_TEMPLATES).copy())
    
    return quests


# ============ РЕФЕРАЛЬНАЯ СИСТЕМА ============
REFERRAL_BONUS = {
    "referrer": {"stars": 10, "gold": 500},  # Тому кто пригласил
    "referee": {"stars": 5, "gold": 200},   # Тому кого пригласили
}


# ============ ХЕЛПЕРЫ ============
def format_item_short(item: dict) -> str:
    """Короткое описание предмета"""
    emoji = RARITY_EMOJI.get(item.get("rarity", "common"), "⚪")
    return f"{emoji} {item.get('name', '???')}"


def format_item_full(item: dict) -> str:
    """Полное описание предмета"""
    emoji = RARITY_EMOJI.get(item.get("rarity", "common"), "⚪")
    rarity_name = RARITY_NAMES.get(item.get("rarity", "common"), "???")
    theme_name = item.get("theme_name", "???")
    
    lines = [
        f"{emoji} <b>{item.get('name', '???')}</b>",
        f"📊 {rarity_name} • {theme_name}",
        f"💪 Сила: {item.get('power', 0)}",
        f"🍀 Удача: {item.get('luck', 0)}",
        f"✨ Магия: {item.get('magic', 0)}",
    ]
    
    if item.get("special_effects"):
        lines.append(f"🌟 {', '.join(item['special_effects'])}")
    
    if item.get("description"):
        lines.append(f"<i>{item['description']}</i>")
    
    return "\n".join(lines)


def get_collection_stats(collection: list) -> dict:
    """Статистика коллекции"""
    stats = {
        "total": len(collection),
        "by_rarity": {},
        "by_theme": {},
        "total_power": 0,
        "total_luck": 0,
        "total_magic": 0,
    }
    
    for item in collection:
        rarity = item.get("rarity", "common")
        theme = item.get("theme", "unknown")
        
        stats["by_rarity"][rarity] = stats["by_rarity"].get(rarity, 0) + 1
        stats["by_theme"][theme] = stats["by_theme"].get(theme, 0) + 1
        stats["total_power"] += item.get("power", 0)
        stats["total_luck"] += item.get("luck", 0)
        stats["total_magic"] += item.get("magic", 0)
    
    return stats

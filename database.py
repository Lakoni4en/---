"""
🗄 База данных "Бесконечная гача"
"""
import aiosqlite
import json
from datetime import datetime, timedelta
from config import DATABASE_PATH


async def init_db():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""CREATE TABLE IF NOT EXISTS players (
            user_id INTEGER PRIMARY KEY,
            username TEXT DEFAULT '',
            first_name TEXT DEFAULT '',
            gold INTEGER DEFAULT 1000,
            stars INTEGER DEFAULT 0,
            free_pulls_today INTEGER DEFAULT 0,
            free_pulls_reset_date TEXT DEFAULT '',
            total_pulls INTEGER DEFAULT 0,
            referrer_id INTEGER,
            daily_streak INTEGER DEFAULT 0,
            last_daily TEXT DEFAULT '',
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
        
        await db.execute("""CREATE TABLE IF NOT EXISTS collection (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            unique_id TEXT UNIQUE,
            name TEXT,
            description TEXT,
            rarity TEXT,
            theme TEXT,
            theme_name TEXT,
            power INTEGER DEFAULT 0,
            luck REAL DEFAULT 0,
            magic INTEGER DEFAULT 0,
            special_effects TEXT,
            obtained_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES players(user_id)
        )""")
        
        await db.execute("""CREATE TABLE IF NOT EXISTS quests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            quest_type TEXT,
            description TEXT,
            target INTEGER,
            progress INTEGER DEFAULT 0,
            reward_gold INTEGER DEFAULT 0,
            reward_stars INTEGER DEFAULT 0,
            is_completed INTEGER DEFAULT 0,
            is_claimed INTEGER DEFAULT 0,
            date TEXT,
            FOREIGN KEY (user_id) REFERENCES players(user_id)
        )""")
        
        await db.commit()


# ======== ИГРОКИ ========
async def get_player(user_id: int) -> dict | None:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM players WHERE user_id = ?", (user_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def create_player(user_id: int, username: str, first_name: str, referrer_id: int = None):
    from config import START_GOLD, START_STARS
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""INSERT OR IGNORE INTO players 
            (user_id, username, first_name, gold, stars, referrer_id) 
            VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, username, first_name, START_GOLD, START_STARS, referrer_id))
        await db.commit()


async def update_player_name(user_id: int, username: str, first_name: str):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE players SET username=?, first_name=? WHERE user_id=?",
            (username, first_name, user_id))
        await db.commit()


# ======== РЕСУРСЫ ========
async def add_gold(user_id: int, amount: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE players SET gold=gold+? WHERE user_id=?", (amount, user_id))
        await db.commit()


async def add_stars(user_id: int, amount: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE players SET stars=stars+? WHERE user_id=?", (amount, user_id))
        await db.commit()


async def spend_gold(user_id: int, amount: int) -> bool:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("SELECT gold FROM players WHERE user_id=?", (user_id,))
        row = await cur.fetchone()
        if not row or row[0] < amount:
            return False
        await db.execute("UPDATE players SET gold=gold-? WHERE user_id=?", (amount, user_id))
        await db.commit()
        return True


async def spend_stars(user_id: int, amount: int) -> bool:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("SELECT stars FROM players WHERE user_id=?", (user_id,))
        row = await cur.fetchone()
        if not row or row[0] < amount:
            return False
        await db.execute("UPDATE players SET stars=stars-? WHERE user_id=?", (amount, user_id))
        await db.commit()
        return True


# ======== БЕСПЛАТНЫЕ ТЯГИ ========
async def get_free_pulls_left(user_id: int) -> int:
    from config import DAILY_FREE_PULLS
    player = await get_player(user_id)
    if not player:
        return 0
    
    today = datetime.now().strftime("%Y-%m-%d")
    if player["free_pulls_reset_date"] != today:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute("UPDATE players SET free_pulls_today=0, free_pulls_reset_date=? WHERE user_id=?",
                (today, user_id))
            await db.commit()
        return DAILY_FREE_PULLS
    
    return max(0, DAILY_FREE_PULLS - player["free_pulls_today"])


async def use_free_pull(user_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE players SET free_pulls_today=free_pulls_today+1, total_pulls=total_pulls+1 WHERE user_id=?",
            (user_id,))
        await db.commit()


async def use_premium_pull(user_id: int, count: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE players SET total_pulls=total_pulls+? WHERE user_id=?", (count, user_id))
        await db.commit()


# ======== КОЛЛЕКЦИЯ ========
async def add_to_collection(user_id: int, item: dict):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""INSERT OR IGNORE INTO collection 
            (user_id, unique_id, name, description, rarity, theme, theme_name, 
             power, luck, magic, special_effects) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, item["unique_id"], item["name"], item.get("description", ""),
             item["rarity"], item["theme"], item["theme_name"],
             item["power"], item["luck"], item["magic"],
             json.dumps(item.get("special_effects", []), ensure_ascii=False)))
        await db.commit()


async def get_collection(user_id: int, limit: int = None, offset: int = 0) -> list:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        query = "SELECT * FROM collection WHERE user_id=? ORDER BY obtained_at DESC"
        params = [user_id]
        if limit:
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])
        cur = await db.execute(query, params)
        rows = await cur.fetchall()
        items = []
        for row in rows:
            item = dict(row)
            if item.get("special_effects"):
                try:
                    item["special_effects"] = json.loads(item["special_effects"])
                except:
                    item["special_effects"] = []
            items.append(item)
        return items


async def get_collection_count(user_id: int) -> int:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("SELECT COUNT(*) FROM collection WHERE user_id=?", (user_id,))
        return (await cur.fetchone())[0]


async def has_item(user_id: int, unique_id: str) -> bool:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("SELECT 1 FROM collection WHERE user_id=? AND unique_id=?", (user_id, unique_id))
        return await cur.fetchone() is not None


async def get_collection_by_rarity(user_id: int, rarity: str) -> list:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM collection WHERE user_id=? AND rarity=? ORDER BY obtained_at DESC",
            (user_id, rarity))
        rows = await cur.fetchall()
        items = []
        for row in rows:
            item = dict(row)
            if item.get("special_effects"):
                try:
                    item["special_effects"] = json.loads(item["special_effects"])
                except:
                    item["special_effects"] = []
            items.append(item)
        return items


async def get_collection_by_theme(user_id: int, theme: str) -> list:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM collection WHERE user_id=? AND theme=? ORDER BY obtained_at DESC",
            (user_id, theme))
        rows = await cur.fetchall()
        items = []
        for row in rows:
            item = dict(row)
            if item.get("special_effects"):
                try:
                    item["special_effects"] = json.loads(item["special_effects"])
                except:
                    item["special_effects"] = []
            items.append(item)
        return items


# ======== КВЕСТЫ ========
async def get_daily_quests(user_id: int) -> list:
    today = datetime.now().strftime("%Y-%m-%d")
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM quests WHERE user_id=? AND date=?", (user_id, today))
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


async def create_daily_quests(user_id: int, quests: list):
    today = datetime.now().strftime("%Y-%m-%d")
    async with aiosqlite.connect(DATABASE_PATH) as db:
        for q in quests:
            await db.execute("""INSERT INTO quests 
                (user_id, quest_type, description, target, reward_gold, reward_stars, date)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (user_id, q["type"], q["description"], q["target"], q["reward_gold"], q["reward_stars"], today))
        await db.commit()


async def update_quest_progress(user_id: int, quest_type: str, amount: int = 1):
    today = datetime.now().strftime("%Y-%m-%d")
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""UPDATE quests SET progress=MIN(progress+?, target),
            is_completed=CASE WHEN progress+?>=target THEN 1 ELSE 0 END
            WHERE user_id=? AND quest_type=? AND date=? AND is_claimed=0""",
            (amount, amount, user_id, quest_type, today))
        await db.commit()


async def claim_quest(user_id: int, quest_id: int) -> dict | None:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM quests WHERE id=? AND user_id=? AND is_completed=1 AND is_claimed=0",
            (quest_id, user_id))
        q = await cur.fetchone()
        if not q:
            return None
        q = dict(q)
        await db.execute("UPDATE quests SET is_claimed=1 WHERE id=?", (quest_id,))
        await db.execute("UPDATE players SET gold=gold+?, stars=stars+? WHERE user_id=?",
            (q["reward_gold"], q["reward_stars"], user_id))
        await db.commit()
        return q


# ======== ЕЖЕДНЕВНЫЙ БОНУС ========
async def check_daily(user_id: int) -> dict | None:
    player = await get_player(user_id)
    if not player:
        return None
    
    today = datetime.now().strftime("%Y-%m-%d")
    if player["last_daily"] == today:
        return None
    
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    new_streak = player["daily_streak"] + 1 if player["last_daily"] == yesterday else 1
    
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE players SET last_daily=?, daily_streak=? WHERE user_id=?",
            (today, new_streak, user_id))
        await db.commit()
    
    return {"daily_streak": new_streak}


# ======== РЕФЕРАЛЫ ========
async def get_referrals_count(user_id: int) -> int:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("SELECT COUNT(*) FROM players WHERE referrer_id=?", (user_id,))
        return (await cur.fetchone())[0]


# ======== ЛИДЕРБОРД ========
async def get_leaderboard(limit: int = 10) -> list:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("""SELECT user_id, username, first_name, 
            (SELECT COUNT(*) FROM collection WHERE collection.user_id=players.user_id) as collection_size,
            total_pulls
            FROM players 
            ORDER BY collection_size DESC, total_pulls DESC
            LIMIT ?""", (limit,))
        rows = await cur.fetchall()
        return [
            {
                "user_id": r[0],
                "username": r[1],
                "first_name": r[2],
                "collection_size": r[3],
                "total_pulls": r[4],
            }
            for r in rows
        ]


async def get_player_rank(user_id: int) -> int:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("""SELECT COUNT(*)+1 FROM players
            WHERE (SELECT COUNT(*) FROM collection WHERE collection.user_id=players.user_id) >
            (SELECT COUNT(*) FROM collection WHERE collection.user_id=?)""", (user_id,))
        return (await cur.fetchone())[0]


# ======== СТАТИСТИКА ========
async def get_bot_stats() -> dict:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        total_players = (await (await db.execute("SELECT COUNT(*) FROM players")).fetchone())[0]
        total_items = (await (await db.execute("SELECT COUNT(*) FROM collection")).fetchone())[0]
        total_pulls = (await (await db.execute("SELECT SUM(total_pulls) FROM players")).fetchone())[0] or 0
        return {
            "total_players": total_players,
            "total_items": total_items,
            "total_pulls": total_pulls,
        }

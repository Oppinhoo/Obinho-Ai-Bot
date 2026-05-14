import aiosqlite
import asyncio
from datetime import datetime
from obinho_bot.config import DB_PATH


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                language TEXT DEFAULT 'en',
                joined_at TEXT,
                last_active TEXT,
                total_requests INTEGER DEFAULT 0
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id TEXT UNIQUE,
                user_id INTEGER,
                client_name TEXT,
                whatsapp TEXT,
                service TEXT,
                details TEXT,
                status TEXT DEFAULT 'pending',
                created_at TEXT,
                language TEXT DEFAULT 'en'
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS course_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                course_name TEXT,
                lesson_number INTEGER DEFAULT 1,
                completed INTEGER DEFAULT 0,
                started_at TEXT,
                updated_at TEXT,
                UNIQUE(user_id, course_name)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS spam_log (
                user_id INTEGER,
                action TEXT,
                timestamp TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event TEXT,
                user_id INTEGER,
                data TEXT,
                timestamp TEXT
            )
        """)
        await db.commit()


async def upsert_user(user_id: int, username: str, full_name: str, language: str = "en"):
    now = datetime.utcnow().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO users (user_id, username, full_name, language, joined_at, last_active)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username=excluded.username,
                full_name=excluded.full_name,
                last_active=excluded.last_active
        """, (user_id, username, full_name, language, now, now))
        await db.commit()


async def update_user_language(user_id: int, language: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET language=? WHERE user_id=?", (language, user_id))
        await db.commit()


async def get_user_language(user_id: int) -> str:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT language FROM users WHERE user_id=?", (user_id,)) as cur:
            row = await cur.fetchone()
            return row[0] if row else "en"


async def save_request(request_id: str, user_id: int, client_name: str,
                       whatsapp: str, service: str, details: str, language: str):
    now = datetime.utcnow().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO requests (request_id, user_id, client_name, whatsapp, service, details, created_at, language)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (request_id, user_id, client_name, whatsapp, service, details, now, language))
        await db.execute("UPDATE users SET total_requests=total_requests+1 WHERE user_id=?", (user_id,))
        await db.commit()


async def get_user_requests(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT request_id, service, status, created_at FROM requests WHERE user_id=? ORDER BY created_at DESC LIMIT 10",
            (user_id,)
        ) as cur:
            return await cur.fetchall()


async def get_all_stats():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cur:
            total_users = (await cur.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM requests") as cur:
            total_requests = (await cur.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM requests WHERE status='pending'") as cur:
            pending = (await cur.fetchone())[0]
        async with db.execute(
            "SELECT service, COUNT(*) as cnt FROM requests GROUP BY service ORDER BY cnt DESC LIMIT 5"
        ) as cur:
            top_services = await cur.fetchall()
        async with db.execute(
            "SELECT language, COUNT(*) as cnt FROM users GROUP BY language ORDER BY cnt DESC"
        ) as cur:
            lang_stats = await cur.fetchall()
    return {
        "total_users": total_users,
        "total_requests": total_requests,
        "pending_requests": pending,
        "top_services": top_services,
        "language_stats": lang_stats,
    }


async def get_or_create_progress(user_id: int, course_name: str):
    now = datetime.utcnow().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT lesson_number, completed FROM course_progress WHERE user_id=? AND course_name=?",
            (user_id, course_name)
        ) as cur:
            row = await cur.fetchone()
        if not row:
            await db.execute("""
                INSERT INTO course_progress (user_id, course_name, lesson_number, completed, started_at, updated_at)
                VALUES (?, ?, 1, 0, ?, ?)
            """, (user_id, course_name, now, now))
            await db.commit()
            return 1, 0
        return row[0], row[1]


async def update_progress(user_id: int, course_name: str, lesson_number: int):
    now = datetime.utcnow().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE course_progress SET lesson_number=?, updated_at=?
            WHERE user_id=? AND course_name=?
        """, (lesson_number, now, user_id, course_name))
        await db.commit()


async def log_spam(user_id: int, action: str):
    now = datetime.utcnow().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO spam_log VALUES (?, ?, ?)", (user_id, action, now))
        await db.commit()


async def count_recent_requests(user_id: int, seconds: int = 3600) -> int:
    from datetime import timedelta
    cutoff = (datetime.utcnow() - timedelta(seconds=seconds)).isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT COUNT(*) FROM requests WHERE user_id=? AND created_at > ?",
            (user_id, cutoff)
        ) as cur:
            row = await cur.fetchone()
            return row[0] if row else 0


async def log_event(event: str, user_id: int, data: str = ""):
    now = datetime.utcnow().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO analytics (event, user_id, data, timestamp) VALUES (?, ?, ?, ?)",
            (event, user_id, data, now)
        )
        await db.commit()

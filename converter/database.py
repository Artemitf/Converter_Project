import aiosqlite
from datetime import datetime
from typing import List, Tuple

DATABASE_NAME = "currency_bot.db"


async def init_db():
    async with aiosqlite.connect(DATABASE_NAME) as db:
        # пользователи
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                registered_at TIMESTAMP
            )
        """
        )

        # избранное
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                position INTEGER,
                currency1 TEXT,
                currency2 TEXT,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            )
        """
        )

        # уведомления
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                asset TEXT,
                percent_change REAL,
                last_triggered TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            )
        """
        )

        await db.commit()


# Регистрация пользователя
async def register_user(user_id: int):
    async with aiosqlite.connect(DATABASE_NAME) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, registered_at) VALUES (?, ?)",
            (user_id, datetime.now().isoformat()),
        )
        await db.commit()


# Работа с избранным
async def get_favorites_with_positions(user_id: int) -> List[Tuple]:
    async with aiosqlite.connect(DATABASE_NAME) as db:

        await db.execute(
            """
            CREATE TEMP TABLE IF NOT EXISTS all_positions (position INTEGER)
        """
        )

        await db.execute("DELETE FROM all_positions")
        for i in range(1, 6):
            await db.execute("INSERT INTO all_positions VALUES (?)", (i,))

        cursor = await db.execute(
            """
            SELECT p.position, f.currency1, f.currency2 
            FROM all_positions p
            LEFT JOIN favorites f ON p.position = f.position AND f.user_id = ?
            ORDER BY p.position
        """,
            (user_id,),
        )

        result = await cursor.fetchall()
        return result


async def update_favorite(user_id: int, position: int, currency1: str, currency2: str):
    async with aiosqlite.connect(DATABASE_NAME) as db:
        # удаляем запись
        await db.execute(
            "DELETE FROM favorites WHERE user_id = ? AND position = ?",
            (user_id, position),
        )

        # добавляем новую
        await db.execute(
            """INSERT INTO favorites (user_id, position, currency1, currency2)
               VALUES (?, ?, ?, ?)""",
            (user_id, position, currency1.upper(), currency2.upper()),
        )
        await db.commit()


# Работа с уведомлениями
async def get_notifications_by_user(user_id: int):
    async with aiosqlite.connect(DATABASE_NAME) as db:
        cursor = await db.execute(
            "SELECT asset, percent_change FROM notifications WHERE user_id = ?",
            (user_id,),
        )
        return await cursor.fetchall()


async def add_notification(user_id: int, asset: str, percent_change: float):
    async with aiosqlite.connect(DATABASE_NAME) as db:
        await db.execute(
            "INSERT INTO notifications (user_id, asset, percent_change, last_triggered) VALUES (?, ?, ?, ?)",
            (user_id, asset.upper(), percent_change, None),
        )
        await db.commit()


async def get_all_notifications():
    async with aiosqlite.connect(DATABASE_NAME) as db:
        cursor = await db.execute(
            "SELECT user_id, asset, percent_change, last_triggered FROM notifications"
        )
        return await cursor.fetchall()


async def update_notification_time(user_id: int, asset: str):
    async with aiosqlite.connect(DATABASE_NAME) as db:
        await db.execute(
            "UPDATE notifications SET last_triggered = ? WHERE user_id = ? AND asset = ?",
            (datetime.now().isoformat(), user_id, asset),
        )
        await db.commit()


async def delete_notification(user_id: int, asset: str):
    async with aiosqlite.connect(DATABASE_NAME) as db:
        await db.execute(
            "DELETE FROM notifications WHERE user_id = ? AND asset = ?",
            (user_id, asset.upper()),
        )
        await db.commit()
        return True

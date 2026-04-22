from __future__ import annotations

import aiosqlite
import random
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "texnopark.db"


async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS fsm_state (
                sk TEXT PRIMARY KEY NOT NULL,
                state TEXT,
                data_json TEXT NOT NULL DEFAULT '{}'
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_user_id INTEGER NOT NULL,
                username TEXT,
                otm TEXT NOT NULL DEFAULT '',
                ism TEXT NOT NULL,
                familya TEXT NOT NULL,
                phone TEXT NOT NULL,
                problem TEXT NOT NULL,
                code TEXT NOT NULL UNIQUE,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL
            )
            """
        )
        await db.commit()

    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("PRAGMA table_info(submissions)")
        cols = {row[1] for row in await cur.fetchall()}
        if "otm" not in cols:
            await db.execute(
                "ALTER TABLE submissions ADD COLUMN otm TEXT NOT NULL DEFAULT ''"
            )
            await db.commit()


async def code_exists(code: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT 1 FROM submissions WHERE code = ?", (code,))
        return await cur.fetchone() is not None


async def generate_unique_code() -> str:
    for _ in range(500):
        c = f"{random.randint(0, 99):02d}"
        if not await code_exists(c):
            return c
    raise RuntimeError("Kodlar tugadi — bazani tekshiring yoki kod uzunligini oshiring")


async def add_submission(
    telegram_user_id: int,
    username: str | None,
    otm: str,
    ism: str,
    familya: str,
    phone: str,
    problem: str,
) -> tuple[int, str]:
    code = await generate_unique_code()
    created = datetime.utcnow().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """
            INSERT INTO submissions
            (telegram_user_id, username, otm, ism, familya, phone, problem, code, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)
            """,
            (
                telegram_user_id,
                username or "",
                otm,
                ism,
                familya,
                phone,
                problem,
                code,
                created,
            ),
        )
        await db.commit()
        return cur.lastrowid, code


async def get_by_id(row_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM submissions WHERE id = ?", (row_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def set_status(row_id: int, status: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "UPDATE submissions SET status = ? WHERE id = ? AND status = 'pending'",
            (status, row_id),
        )
        await db.commit()
        return cur.rowcount > 0


async def list_pending():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM submissions WHERE status = 'pending' ORDER BY id ASC"
        )
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


async def status_counts() -> dict[str, int]:
    async with aiosqlite.connect(DB_PATH) as db_c:
        cur = await db_c.execute(
            "SELECT status, COUNT(*) FROM submissions GROUP BY status"
        )
        rows = await cur.fetchall()
        out: dict[str, int] = {}
        for status, n in rows:
            out[str(status)] = int(n)
        return out


async def list_by_status(status: str, *, limit: int = 100):
    lim = max(1, min(limit, 500))
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            """
            SELECT * FROM submissions
            WHERE status = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (status, lim),
        )
        rows = await cur.fetchall()
        return [dict(r) for r in rows]

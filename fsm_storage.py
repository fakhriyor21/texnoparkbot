"""FSM holatlari — SQLite (`texnopark.db` bilan bir fayl)."""

from __future__ import annotations

import json
from copy import copy
from pathlib import Path
from typing import Any, Mapping

import aiosqlite
from aiogram.exceptions import DataNotDictLikeError
from aiogram.fsm.state import State
from aiogram.fsm.storage.base import BaseStorage, StateType, StorageKey

from db import DB_PATH


def _storage_key_str(key: StorageKey) -> str:
    tid = 0 if key.thread_id is None else key.thread_id
    bc = key.business_connection_id or ""
    return f"{key.bot_id}:{key.chat_id}:{key.user_id}:{tid}:{bc}:{key.destiny}"


class SQLiteFSMStorage(BaseStorage):
    def __init__(self, db_path: Path | str | None = None) -> None:
        self._path = Path(db_path) if db_path is not None else DB_PATH

    async def set_state(self, key: StorageKey, state: StateType = None) -> None:
        sk = _storage_key_str(key)
        if state is None:
            st: str | None = None
        elif isinstance(state, State):
            st = state.state
        else:
            st = state

        async with aiosqlite.connect(self._path) as conn:
            cur = await conn.execute(
                "SELECT 1 FROM fsm_state WHERE sk = ?", (sk,)
            )
            exists = await cur.fetchone()
            if exists:
                await conn.execute(
                    "UPDATE fsm_state SET state = ? WHERE sk = ?", (st, sk)
                )
            else:
                await conn.execute(
                    """
                    INSERT INTO fsm_state (sk, state, data_json)
                    VALUES (?, ?, '{}')
                    """,
                    (sk, st),
                )
            await conn.commit()

    async def get_state(self, key: StorageKey) -> str | None:
        sk = _storage_key_str(key)
        async with aiosqlite.connect(self._path) as conn:
            cur = await conn.execute(
                "SELECT state FROM fsm_state WHERE sk = ?", (sk,)
            )
            row = await cur.fetchone()
            return row[0] if row else None

    async def set_data(self, key: StorageKey, data: Mapping[str, Any]) -> None:
        if not isinstance(data, dict):
            raise DataNotDictLikeError(
                f"Data must be a dict or dict-like object, got {type(data).__name__}"
            )
        sk = _storage_key_str(key)
        payload = json.dumps(data, ensure_ascii=False)

        async with aiosqlite.connect(self._path) as conn:
            cur = await conn.execute(
                "SELECT 1 FROM fsm_state WHERE sk = ?", (sk,)
            )
            exists = await cur.fetchone()
            if exists:
                await conn.execute(
                    "UPDATE fsm_state SET data_json = ? WHERE sk = ?",
                    (payload, sk),
                )
            else:
                await conn.execute(
                    """
                    INSERT INTO fsm_state (sk, state, data_json)
                    VALUES (?, NULL, ?)
                    """,
                    (sk, payload),
                )
            await conn.commit()

    async def get_data(self, key: StorageKey) -> dict[str, Any]:
        sk = _storage_key_str(key)
        async with aiosqlite.connect(self._path) as conn:
            cur = await conn.execute(
                "SELECT data_json FROM fsm_state WHERE sk = ?", (sk,)
            )
            row = await cur.fetchone()
            if not row or not row[0]:
                return {}
            try:
                out = json.loads(row[0])
                return out if isinstance(out, dict) else {}
            except json.JSONDecodeError:
                return {}

    async def get_value(
        self,
        storage_key: StorageKey,
        dict_key: str,
        default: Any | None = None,
    ) -> Any | None:
        data = await self.get_data(storage_key)
        return copy(data.get(dict_key, default))

    async def close(self) -> None:
        pass

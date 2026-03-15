from __future__ import annotations

import aiosqlite
from loguru import logger

from crypto_alert_bot.models.schemas import Alert, AlertDirection, AlertStatus, User, UserPreferences
from crypto_alert_bot.utils.exceptions import DatabaseError

CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT DEFAULT '',
    preferred_exchange TEXT DEFAULT 'binance',
    preferred_currency TEXT DEFAULT 'USD',
    created_at TEXT NOT NULL
)
"""

CREATE_ALERTS_TABLE = """
CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    symbol TEXT NOT NULL,
    target_price REAL NOT NULL,
    direction TEXT NOT NULL,
    exchange TEXT DEFAULT 'binance',
    status TEXT DEFAULT 'active',
    created_at TEXT NOT NULL,
    triggered_at TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
)
"""

CREATE_PREFERENCES_TABLE = """
CREATE TABLE IF NOT EXISTS preferences (
    user_id INTEGER PRIMARY KEY,
    default_symbols TEXT DEFAULT 'BTC,ETH',
    chart_style TEXT DEFAULT 'dark',
    notification_enabled INTEGER DEFAULT 1,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
)
"""


class Database:
    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._connection: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        try:
            self._connection = await aiosqlite.connect(self._db_path)
            self._connection.row_factory = aiosqlite.Row
            await self._connection.execute("PRAGMA journal_mode=WAL")
            await self._connection.execute("PRAGMA foreign_keys=ON")
            await self._connection.execute(CREATE_USERS_TABLE)
            await self._connection.execute(CREATE_ALERTS_TABLE)
            await self._connection.execute(CREATE_PREFERENCES_TABLE)
            await self._connection.commit()
            logger.info("Database connected at {}", self._db_path)
        except Exception as e:
            raise DatabaseError("connect", str(e)) from e

    async def close(self) -> None:
        if self._connection:
            await self._connection.close()
            logger.info("Database connection closed")

    @property
    def conn(self) -> aiosqlite.Connection:
        if self._connection is None:
            raise DatabaseError("access", "Database not connected")
        return self._connection

    async def upsert_user(self, user: User) -> None:
        try:
            await self.conn.execute(
                """INSERT INTO users (user_id, username, preferred_exchange, preferred_currency, created_at)
                   VALUES (?, ?, ?, ?, ?)
                   ON CONFLICT(user_id) DO UPDATE SET
                   username=excluded.username""",
                (user.user_id, user.username, user.preferred_exchange, user.preferred_currency, user.created_at),
            )
            await self.conn.commit()
        except Exception as e:
            raise DatabaseError("upsert_user", str(e)) from e

    async def get_user(self, user_id: int) -> User | None:
        try:
            cursor = await self.conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            row = await cursor.fetchone()
            if row is None:
                return None
            return User(
                user_id=row["user_id"],
                username=row["username"],
                preferred_exchange=row["preferred_exchange"],
                preferred_currency=row["preferred_currency"],
                created_at=row["created_at"],
            )
        except Exception as e:
            raise DatabaseError("get_user", str(e)) from e

    async def create_alert(self, alert: Alert) -> int:
        try:
            cursor = await self.conn.execute(
                """INSERT INTO alerts (user_id, symbol, target_price, direction, exchange, status, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    alert.user_id,
                    alert.symbol,
                    alert.target_price,
                    alert.direction.value,
                    alert.exchange,
                    alert.status.value,
                    alert.created_at,
                ),
            )
            await self.conn.commit()
            return cursor.lastrowid or 0
        except Exception as e:
            raise DatabaseError("create_alert", str(e)) from e

    async def get_user_alerts(self, user_id: int, status: AlertStatus | None = None) -> list[Alert]:
        try:
            if status:
                cursor = await self.conn.execute(
                    "SELECT * FROM alerts WHERE user_id = ? AND status = ? ORDER BY created_at DESC",
                    (user_id, status.value),
                )
            else:
                cursor = await self.conn.execute(
                    "SELECT * FROM alerts WHERE user_id = ? ORDER BY created_at DESC", (user_id,)
                )
            rows = await cursor.fetchall()
            return [
                Alert(
                    id=row["id"],
                    user_id=row["user_id"],
                    symbol=row["symbol"],
                    target_price=row["target_price"],
                    direction=AlertDirection(row["direction"]),
                    exchange=row["exchange"],
                    status=AlertStatus(row["status"]),
                    created_at=row["created_at"],
                    triggered_at=row["triggered_at"],
                )
                for row in rows
            ]
        except Exception as e:
            raise DatabaseError("get_user_alerts", str(e)) from e

    async def get_all_active_alerts(self) -> list[Alert]:
        try:
            cursor = await self.conn.execute("SELECT * FROM alerts WHERE status = ?", (AlertStatus.ACTIVE.value,))
            rows = await cursor.fetchall()
            return [
                Alert(
                    id=row["id"],
                    user_id=row["user_id"],
                    symbol=row["symbol"],
                    target_price=row["target_price"],
                    direction=AlertDirection(row["direction"]),
                    exchange=row["exchange"],
                    status=AlertStatus(row["status"]),
                    created_at=row["created_at"],
                    triggered_at=row["triggered_at"],
                )
                for row in rows
            ]
        except Exception as e:
            raise DatabaseError("get_all_active_alerts", str(e)) from e

    async def update_alert_status(self, alert_id: int, status: AlertStatus, triggered_at: str | None = None) -> None:
        try:
            await self.conn.execute(
                "UPDATE alerts SET status = ?, triggered_at = ? WHERE id = ?",
                (status.value, triggered_at, alert_id),
            )
            await self.conn.commit()
        except Exception as e:
            raise DatabaseError("update_alert_status", str(e)) from e

    async def delete_alert(self, alert_id: int, user_id: int) -> bool:
        try:
            cursor = await self.conn.execute(
                "DELETE FROM alerts WHERE id = ? AND user_id = ?", (alert_id, user_id)
            )
            await self.conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            raise DatabaseError("delete_alert", str(e)) from e

    async def count_user_alerts(self, user_id: int) -> int:
        try:
            cursor = await self.conn.execute(
                "SELECT COUNT(*) as cnt FROM alerts WHERE user_id = ? AND status = ?",
                (user_id, AlertStatus.ACTIVE.value),
            )
            row = await cursor.fetchone()
            return row["cnt"] if row else 0
        except Exception as e:
            raise DatabaseError("count_user_alerts", str(e)) from e

    async def get_preferences(self, user_id: int) -> UserPreferences:
        try:
            cursor = await self.conn.execute("SELECT * FROM preferences WHERE user_id = ?", (user_id,))
            row = await cursor.fetchone()
            if row is None:
                return UserPreferences(user_id=user_id)
            return UserPreferences(
                user_id=row["user_id"],
                default_symbols=[s.strip() for s in row["default_symbols"].split(",")],
                chart_style=row["chart_style"],
                notification_enabled=bool(row["notification_enabled"]),
            )
        except Exception as e:
            raise DatabaseError("get_preferences", str(e)) from e

    async def save_preferences(self, prefs: UserPreferences) -> None:
        try:
            await self.conn.execute(
                """INSERT INTO preferences (user_id, default_symbols, chart_style, notification_enabled)
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT(user_id) DO UPDATE SET
                   default_symbols=excluded.default_symbols,
                   chart_style=excluded.chart_style,
                   notification_enabled=excluded.notification_enabled""",
                (
                    prefs.user_id,
                    ",".join(prefs.default_symbols),
                    prefs.chart_style,
                    int(prefs.notification_enabled),
                ),
            )
            await self.conn.commit()
        except Exception as e:
            raise DatabaseError("save_preferences", str(e)) from e

"""Append-only time-series store for Telegram online-status events.

Collection: online_status_log
Schema:
    user_id    int       — Telegram user ID
    ts         datetime  — UTC timestamp when we polled
    online     bool      — True if user was online at poll time (UserStatusOnline)
    was_online datetime|None — Telegram's last-seen timestamp from UserStatusOffline
"""

from datetime import datetime
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ASCENDING


COLLECTION = "online_status_log"


async def ensure_index(db: AsyncIOMotorDatabase) -> None:
    await db[COLLECTION].create_index(
        [("user_id", ASCENDING), ("ts", ASCENDING)], background=True
    )


async def append_event(
    db: AsyncIOMotorDatabase,
    user_id: int,
    ts: datetime,
    online: bool,
    was_online: Optional[datetime],
) -> None:
    await db[COLLECTION].insert_one(
        {"user_id": user_id, "ts": ts, "online": online, "was_online": was_online}
    )


async def events_in_range(
    db: AsyncIOMotorDatabase,
    user_id: int,
    since: datetime,
    until: datetime,
) -> list[dict]:
    cursor = db[COLLECTION].find(
        {"user_id": user_id, "ts": {"$gte": since, "$lte": until}},
        sort=[("ts", ASCENDING)],
    )
    return await cursor.to_list(length=None)

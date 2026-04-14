from datetime import date, datetime
from typing import Any, Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from src.models import Challenge, ChallengeUser, CheckIn, SleepLog


def _dump(doc: Any) -> dict:
    data = doc.model_dump(by_alias=True, exclude_none=True)
    if data.get("_id") is None:
        data.pop("_id", None)
    return data


class Repo:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.challenges = db["challenges"]
        self.users = db["challenge_users"]
        self.logs = db["sleep_logs"]

    async def ensure_indexes(self) -> None:
        await self.challenges.create_index("code", unique=True)
        await self.users.create_index([("user_id", 1), ("challenge_id", 1)], unique=True)
        await self.logs.create_index(
            [("user_id", 1), ("challenge_id", 1), ("date", 1)], unique=True
        )

    # Challenges

    async def save_challenge(self, c: Challenge) -> ObjectId:
        data = _dump(c)
        if c.id is None:
            res = await self.challenges.insert_one(data)
            c.id = res.inserted_id
            return res.inserted_id
        await self.challenges.replace_one({"_id": c.id}, data, upsert=True)
        return c.id

    async def get_challenge_by_code(self, code: str) -> Optional[Challenge]:
        doc = await self.challenges.find_one({"code": code})
        return Challenge(**doc) if doc else None

    async def get_challenge(self, challenge_id: ObjectId) -> Optional[Challenge]:
        doc = await self.challenges.find_one({"_id": challenge_id})
        return Challenge(**doc) if doc else None

    async def list_challenges(self, include_drafts: bool = True) -> list[Challenge]:
        q: dict = {} if include_drafts else {"status": {"$ne": "draft"}}
        cursor = self.challenges.find(q).sort("created_at", -1)
        return [Challenge(**d) async for d in cursor]

    async def list_active_challenges(self) -> list[Challenge]:
        cursor = self.challenges.find({"status": "active"})
        return [Challenge(**d) async for d in cursor]

    # Users

    async def save_user(self, u: ChallengeUser) -> ObjectId:
        data = _dump(u)
        if u.id is None:
            res = await self.users.insert_one(data)
            u.id = res.inserted_id
            return res.inserted_id
        await self.users.replace_one({"_id": u.id}, data, upsert=True)
        return u.id

    async def get_user(self, user_id: int, challenge_id: ObjectId) -> Optional[ChallengeUser]:
        doc = await self.users.find_one({"user_id": user_id, "challenge_id": challenge_id})
        return ChallengeUser(**doc) if doc else None

    async def active_users_for_challenge(self, challenge_id: ObjectId) -> list[ChallengeUser]:
        cursor = self.users.find({"challenge_id": challenge_id, "active": True})
        return [ChallengeUser(**d) async for d in cursor]

    async def active_memberships_for_user(self, user_id: int) -> list[ChallengeUser]:
        cursor = self.users.find({"user_id": user_id, "active": True})
        return [ChallengeUser(**d) async for d in cursor]

    # Sleep logs

    async def upsert_log(self, log: SleepLog) -> None:
        data = _dump(log)
        await self.logs.update_one(
            {"user_id": log.user_id, "challenge_id": log.challenge_id, "date": log.date},
            {"$set": data},
            upsert=True,
        )

    async def get_log(
        self, user_id: int, challenge_id: ObjectId, day: date
    ) -> Optional[SleepLog]:
        doc = await self.logs.find_one(
            {"user_id": user_id, "challenge_id": challenge_id, "date": day}
        )
        return SleepLog(**doc) if doc else None

    async def set_check_in(
        self,
        user_id: int,
        challenge_id: ObjectId,
        day: date,
        field: str,
        check_in: CheckIn,
    ) -> None:
        assert field in ("bed", "wake")
        await self.logs.update_one(
            {"user_id": user_id, "challenge_id": challenge_id, "date": day},
            {
                "$setOnInsert": {
                    "user_id": user_id,
                    "challenge_id": challenge_id,
                    "date": day,
                    "score": 0.0,
                    "streak_after": 0,
                    "finalized": False,
                },
                "$set": {field: check_in.model_dump()},
            },
            upsert=True,
        )

    async def set_online_seen(
        self, user_id: int, challenge_id: ObjectId, day: date, seen: datetime
    ) -> None:
        await self.logs.update_one(
            {"user_id": user_id, "challenge_id": challenge_id, "date": day},
            {
                "$setOnInsert": {
                    "user_id": user_id,
                    "challenge_id": challenge_id,
                    "date": day,
                    "score": 0.0,
                    "streak_after": 0,
                    "finalized": False,
                },
                "$set": {"online_last_seen": seen},
            },
            upsert=True,
        )

    async def recent_logs(
        self, user_id: int, challenge_id: ObjectId, limit: int = 14
    ) -> list[SleepLog]:
        cursor = (
            self.logs.find({"user_id": user_id, "challenge_id": challenge_id})
            .sort("date", -1)
            .limit(limit)
        )
        return [SleepLog(**d) async for d in cursor]

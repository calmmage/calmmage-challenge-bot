from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from loguru import logger

from src._app import App


class ServiceAccountClient:
    _instance: Optional["ServiceAccountClient"] = None

    def __init__(self, api_id: int, api_hash: str, session_path: Path):
        self.api_id = api_id
        self.api_hash = api_hash
        self.session_path = session_path
        self.session_path.parent.mkdir(parents=True, exist_ok=True)
        self._client = None  # TelegramClient instance

    async def _get_or_create_client(self):
        if self._client is not None:
            return self._client
        from telethon import TelegramClient

        self._client = TelegramClient(
            str(self.session_path), self.api_id, self.api_hash
        )
        await self._client.connect()
        return self._client

    async def connect_if_authorized(self) -> bool:
        client = await self._get_or_create_client()
        if await client.is_user_authorized():
            me = await client.get_me()
            logger.info(f"Service account authorized as {me.username or me.phone}")
            return True
        logger.info("Service account not yet authorized; /service_auth required")
        return False

    async def send_code(self, phone: str) -> str:
        client = await self._get_or_create_client()
        result = await client.send_code_request(phone)
        return result.phone_code_hash

    async def sign_in(
        self, phone: str, code: str, phone_code_hash: str, password: str | None = None
    ) -> None:
        client = await self._get_or_create_client()
        try:
            await client.sign_in(phone, code, phone_code_hash=phone_code_hash)
        except Exception as e:
            if "password" in str(e).lower() and password:
                await client.sign_in(password=password)
            else:
                raise

    async def get_last_seen(self, user_id: int) -> datetime | None:
        client = await self._get_or_create_client()
        if not await client.is_user_authorized():
            return None
        try:
            entity = await client.get_entity(user_id)
            status = getattr(entity, "status", None)
            if status is None:
                return None
            cls = status.__class__.__name__
            if cls == "UserStatusOnline":
                return datetime.now(timezone.utc).replace(tzinfo=None)
            was_online = getattr(status, "was_online", None)
            if was_online:
                return was_online.replace(tzinfo=None) if was_online.tzinfo else was_online
        except Exception as e:
            logger.debug(f"get_last_seen({user_id}) failed: {e}")
        return None

    async def disconnect(self) -> None:
        if self._client is not None:
            await self._client.disconnect()
            self._client = None


def init_service_client(app: App) -> ServiceAccountClient:
    assert app.config.sleep_bot_service_api_id is not None
    assert app.config.sleep_bot_service_api_hash is not None
    client = ServiceAccountClient(
        api_id=app.config.sleep_bot_service_api_id,
        api_hash=app.config.sleep_bot_service_api_hash.get_secret_value(),
        session_path=app.service_session_path,
    )
    ServiceAccountClient._instance = client
    return client


def get_service_client() -> ServiceAccountClient | None:
    return ServiceAccountClient._instance

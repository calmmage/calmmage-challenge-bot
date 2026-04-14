from pathlib import Path
from typing import Optional

from pydantic import SecretStr
from pydantic_settings import BaseSettings


class AppConfig(BaseSettings):
    """App configuration loaded from env."""

    telegram_bot_token: SecretStr

    sleep_bot_service_phone: Optional[str] = None
    sleep_bot_service_api_id: Optional[int] = None
    sleep_bot_service_api_hash: Optional[SecretStr] = None
    sleep_bot_service_session_path: str = "sessions/service_account"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


class App:
    name = "Calmmage Sleep Challenge Bot"

    def __init__(self, **kwargs):
        self.config = AppConfig(**kwargs)

    @property
    def service_session_path(self) -> Path:
        return Path(self.config.sleep_bot_service_session_path)

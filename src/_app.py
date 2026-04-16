from pydantic import SecretStr
from pydantic_settings import BaseSettings


class AppConfig(BaseSettings):
    """App configuration. Everything else (Mongo, Telethon, admins, scheduler…)
    is owned by botspot via its BOTSPOT_* env vars."""

    telegram_bot_token: SecretStr

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


class App:
    name = "Calmmage Sleep Challenge Bot"

    def __init__(self, **kwargs):
        self.config = AppConfig(**kwargs)

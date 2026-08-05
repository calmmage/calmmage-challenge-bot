from typing import Optional

from pydantic_settings import BaseSettings


class SleepMonitorConfig(BaseSettings):
    """Private feature: poll one user's Telegram status and infer sleep/wake times.

    Disabled by default — set SLEEP_MONITOR_TARGET_ID to enable.
    """

    sleep_monitor_target_id: Optional[int] = None
    sleep_monitor_interval_minutes: int = 10
    sleep_monitor_morning_hour: int = 8
    sleep_monitor_morning_tz: str = "UTC"
    # Where to DM the morning report; defaults to the target user themselves.
    sleep_monitor_admin_chat_id: Optional[int] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    @property
    def enabled(self) -> bool:
        return self.sleep_monitor_target_id is not None

    @property
    def report_chat_id(self) -> Optional[int]:
        return self.sleep_monitor_admin_chat_id or self.sleep_monitor_target_id

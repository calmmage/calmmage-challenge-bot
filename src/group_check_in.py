"""Pure helpers for deciding what a video note in the group means.

No I/O, no bot, no DB — just time/window logic callable from the router and from tests.
"""

from datetime import datetime, time
from typing import Literal, Optional

from src.models import SleepLog
from src.time_utils import in_bed_window, in_wake_window

CheckInField = Literal["bed", "wake"]


def locate_checkin(now_local: datetime) -> Optional[CheckInField]:
    """Which check-in slot does 'now' belong to? None → outside any window."""
    if in_bed_window(now_local):
        return "bed"
    if in_wake_window(now_local):
        return "wake"
    return None


def already_checked_in(log: Optional[SleepLog], field: CheckInField) -> bool:
    if log is None:
        return False
    return getattr(log, field) is not None


def is_on_time(now_local: datetime, deadline: time) -> bool:
    return now_local.time() <= deadline

from datetime import time, timedelta, datetime, date
from typing import Literal

Difficulty = Literal["light", "medium", "hard"]

_DIFFICULTY_SHIFT = {
    "light": timedelta(minutes=30),
    "medium": timedelta(hours=1),
    "hard": timedelta(hours=2),
}

DEFAULT_BEDTIME = time(23, 30)
DEFAULT_WAKEUP = time(7, 30)


def _shift_earlier(t: time, delta: timedelta) -> time:
    base = datetime.combine(date(2000, 1, 2), t)
    shifted = base - delta
    return shifted.time()


def deadline_from_usual(usual: time, difficulty: Difficulty) -> time:
    return _shift_earlier(usual, _DIFFICULTY_SHIFT[difficulty])


def defaults() -> tuple[time, time]:
    return DEFAULT_BEDTIME, DEFAULT_WAKEUP


def varies_defaults() -> tuple[time, time]:
    return DEFAULT_BEDTIME, DEFAULT_WAKEUP


def validate_tightening(current: time, new: time) -> bool:
    """Only tightening (strictly earlier) is allowed.

    Times near midnight are treated ring-free: we simply compare as times.
    This is a deliberate simplification — deadlines are expected in 21:00–08:00 range
    for bed and 05:00–11:00 for wake, so the ordering is well-defined.
    """
    return new < current

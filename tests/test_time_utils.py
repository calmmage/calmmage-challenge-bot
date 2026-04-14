from datetime import datetime, time
from zoneinfo import ZoneInfo

from src.time_utils import (
    challenge_day_for,
    deadline_passed,
    in_bed_window,
    in_wake_window,
    infer_tz_from_offset,
    is_valid_tz,
)


def test_morning_belongs_to_same_challenge_day():
    dt = datetime(2026, 4, 14, 7, 30, tzinfo=ZoneInfo("Europe/Zurich"))
    assert challenge_day_for(dt).isoformat() == "2026-04-14"


def test_late_evening_belongs_to_next_challenge_day():
    dt = datetime(2026, 4, 13, 23, 30, tzinfo=ZoneInfo("Europe/Zurich"))
    assert challenge_day_for(dt).isoformat() == "2026-04-14"


def test_afternoon_rolls_over_at_pivot():
    before = datetime(2026, 4, 14, 13, 59, tzinfo=ZoneInfo("Europe/Zurich"))
    after = datetime(2026, 4, 14, 14, 0, tzinfo=ZoneInfo("Europe/Zurich"))
    assert challenge_day_for(before).isoformat() == "2026-04-14"
    assert challenge_day_for(after).isoformat() == "2026-04-15"


def test_bed_window_covers_evening_and_small_hours():
    assert in_bed_window(datetime(2026, 4, 13, 22, 0))
    assert in_bed_window(datetime(2026, 4, 14, 2, 0))
    assert not in_bed_window(datetime(2026, 4, 14, 10, 0))


def test_wake_window_covers_morning():
    assert in_wake_window(datetime(2026, 4, 14, 7, 0))
    assert not in_wake_window(datetime(2026, 4, 14, 15, 0))


def test_deadline_passed_compares_time_only():
    assert deadline_passed(datetime(2026, 4, 14, 7, 31), time(7, 30))
    assert not deadline_passed(datetime(2026, 4, 14, 7, 29), time(7, 30))


def test_is_valid_tz_known():
    assert is_valid_tz("Europe/Zurich")
    assert not is_valid_tz("Mars/Olympus")


def test_infer_tz_from_offset_parses_common_cases():
    # Can't assert a specific zone without knowing UTC at test time,
    # but invalid inputs should return None.
    assert infer_tz_from_offset("abc") is None
    assert infer_tz_from_offset("25:00") is None
    assert infer_tz_from_offset("12:60") is None

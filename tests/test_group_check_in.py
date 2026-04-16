from datetime import date, datetime, time

from bson import ObjectId

from src.group_check_in import already_checked_in, is_on_time, locate_checkin
from src.models import CheckIn, SleepLog


def test_late_evening_is_bed():
    assert locate_checkin(datetime(2026, 4, 13, 22, 30)) == "bed"


def test_small_hours_are_bed():
    assert locate_checkin(datetime(2026, 4, 14, 2, 0)) == "bed"


def test_morning_is_wake():
    assert locate_checkin(datetime(2026, 4, 14, 7, 30)) == "wake"


def test_afternoon_is_neither():
    assert locate_checkin(datetime(2026, 4, 14, 15, 0)) is None


def test_already_checked_in_false_without_log():
    assert already_checked_in(None, "bed") is False


def test_already_checked_in_true_when_bed_logged():
    log = SleepLog(
        user_id=1,
        challenge_id=ObjectId(),
        date=date(2026, 4, 14),
        bed=CheckIn(ts=datetime(2026, 4, 13, 23, 0), kind="video_note", on_time=True),
    )
    assert already_checked_in(log, "bed") is True
    assert already_checked_in(log, "wake") is False


def test_on_time_at_deadline():
    assert is_on_time(datetime(2026, 4, 14, 7, 30), time(7, 30)) is True


def test_on_time_after_deadline():
    assert is_on_time(datetime(2026, 4, 14, 7, 31), time(7, 30)) is False

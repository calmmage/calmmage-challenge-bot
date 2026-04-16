from datetime import date, datetime

from bson import ObjectId

from src.models import CheckIn, SleepLog
from src.scoring import score_day, update_streak


def _log(bed: CheckIn | None, wake: CheckIn | None) -> SleepLog:
    return SleepLog(
        user_id=1,
        challenge_id=ObjectId(),
        date=date(2026, 4, 14),
        bed=bed,
        wake=wake,
    )


def test_both_ontime_video_notes_score_one():
    log = _log(
        CheckIn(ts=datetime(2026, 4, 13, 23, 0), kind="video_note", on_time=True),
        CheckIn(ts=datetime(2026, 4, 14, 7, 0), kind="video_note", on_time=True),
    )
    assert score_day(log) == 1.0


def test_late_video_note_counts_as_half():
    log = _log(
        CheckIn(ts=datetime(2026, 4, 13, 23, 45), kind="video_note", on_time=False),
        CheckIn(ts=datetime(2026, 4, 14, 7, 0), kind="video_note", on_time=True),
    )
    assert score_day(log) == 0.5


def test_missing_wake_is_zero():
    log = _log(
        CheckIn(ts=datetime(2026, 4, 13, 23, 0), kind="video_note", on_time=True),
        None,
    )
    assert score_day(log) == 0.0


def test_text_message_never_counts():
    log = _log(
        CheckIn(ts=datetime(2026, 4, 13, 23, 0), kind="text", on_time=True),
        CheckIn(ts=datetime(2026, 4, 14, 7, 0), kind="video_note", on_time=True),
    )
    assert score_day(log) == 0.0


def test_both_late_scores_half():
    log = _log(
        CheckIn(ts=datetime(2026, 4, 13, 23, 45), kind="video_note", on_time=False),
        CheckIn(ts=datetime(2026, 4, 14, 7, 45), kind="video_note", on_time=False),
    )
    assert score_day(log) == 0.5


def test_streak_increments_on_full_win():
    assert update_streak(5, 1.0, 1.0) == 6


def test_streak_resets_on_zero():
    assert update_streak(5, 0.0, 1.0) == 0


def test_streak_resets_on_two_half_fails():
    assert update_streak(3, 0.5, 0.5) == 0


def test_streak_increments_on_half_after_full():
    assert update_streak(3, 0.5, 1.0) == 4


def test_streak_from_zero_with_half_start():
    assert update_streak(0, 0.5, None) == 1

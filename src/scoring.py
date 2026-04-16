from src.models import SleepLog


def _proof_ok(kind: str | None) -> bool:
    """Only video notes count as valid check-in proof."""
    return kind == "video_note"


def score_day(log: SleepLog) -> float:
    bed_valid = log.bed is not None and _proof_ok(log.bed.kind)
    wake_valid = log.wake is not None and _proof_ok(log.wake.kind)
    if not (bed_valid and wake_valid):
        return 0.0
    assert log.bed is not None and log.wake is not None
    if log.bed.on_time and log.wake.on_time:
        return 1.0
    return 0.5


def update_streak(
    prev_streak: int, today_score: float, yesterday_score: float | None
) -> int:
    if today_score == 0.0:
        return 0
    if today_score == 0.5 and yesterday_score == 0.5:
        return 0
    return prev_streak + 1

from src.models import ProofPolicy, SleepLog, UserProofChoice


def _effective_policy(
    challenge_policy: ProofPolicy, user_choice: UserProofChoice | None
) -> UserProofChoice:
    if challenge_policy == "user_choice":
        return user_choice or "text_or_video"
    return challenge_policy


def _proof_ok(kind: str | None, policy: UserProofChoice) -> bool:
    if kind is None:
        return False
    if policy == "video_only":
        return kind == "video_note"
    return kind in ("text", "video_note")


def score_day(
    log: SleepLog,
    bed_policy: ProofPolicy,
    wake_policy: ProofPolicy,
    bed_choice: UserProofChoice | None = None,
    wake_choice: UserProofChoice | None = None,
) -> float:
    bed_effective = _effective_policy(bed_policy, bed_choice)
    wake_effective = _effective_policy(wake_policy, wake_choice)

    bed_valid = log.bed is not None and _proof_ok(log.bed.kind, bed_effective)
    wake_valid = log.wake is not None and _proof_ok(log.wake.kind, wake_effective)

    if not (bed_valid and wake_valid):
        return 0.0

    assert log.bed is not None and log.wake is not None
    if log.bed.on_time and log.wake.on_time:
        return 1.0
    return 0.5


def update_streak(prev_streak: int, today_score: float, yesterday_score: float | None) -> int:
    if today_score == 0.0:
        return 0
    if today_score == 0.5 and yesterday_score == 0.5:
        return 0
    return prev_streak + 1

"""Heuristic: find sleep / wake times from a night's worth of status events.

Each event is a dict with:
    ts         datetime  — when we polled (UTC)
    online     bool      — True = UserStatusOnline
    was_online datetime|None — Telegram's last-seen from UserStatusOffline

Strategy
--------
For each poll, derive a "last_active" timestamp — the most recent moment we
know the user was online:
  - online=True          → last_active = ts  (they are online RIGHT NOW)
  - was_online within RECENT_THRESHOLD of ts → last_active = was_online
  - otherwise            → no fresh signal (hidden / too old)

Collect all last_active timestamps, sort them, find the biggest gap between
consecutive ones.  If the gap is ≥ MIN_SLEEP_HOURS:
  sleep_time = the activity timestamp just BEFORE the gap
  wake_time  = the activity timestamp just AFTER the gap
"""

from datetime import datetime, timedelta
from typing import Optional

MIN_SLEEP_HOURS = 2.0
RECENT_THRESHOLD = timedelta(minutes=20)


def _last_active(event: dict) -> Optional[datetime]:
    """Extract the most recent activity timestamp from a poll event, or None."""
    if event.get("online"):
        return event["ts"]
    was = event.get("was_online")
    if was and (event["ts"] - was) <= RECENT_THRESHOLD:
        return was
    return None


def find_sleep_wake(
    events: list[dict],
) -> tuple[Optional[datetime], Optional[datetime]]:
    """Return (sleep_time, wake_time) UTC, or (None, None) if undetermined."""
    if len(events) < 2:
        return None, None

    # Collect all moments we know the user was online, deduplicated & sorted.
    activity: list[datetime] = sorted(
        {la for e in events if (la := _last_active(e)) is not None}
    )

    if len(activity) < 2:
        return None, None

    min_gap = timedelta(hours=MIN_SLEEP_HOURS)
    best_gap = timedelta(0)
    sleep_time: Optional[datetime] = None
    wake_time: Optional[datetime] = None

    for i in range(len(activity) - 1):
        gap = activity[i + 1] - activity[i]
        if gap > best_gap and gap >= min_gap:
            best_gap = gap
            sleep_time = activity[i]
            wake_time = activity[i + 1]

    return sleep_time, wake_time


def format_sleep_report(
    sleep_time: Optional[datetime],
    wake_time: Optional[datetime],
    tz_name: str = "UTC",
) -> str:
    """Format a human-readable morning report line."""
    from zoneinfo import ZoneInfo

    tz = ZoneInfo(tz_name)

    def _fmt(dt: Optional[datetime]) -> str:
        if dt is None:
            return "unknown"
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=ZoneInfo("UTC"))
        return dt.astimezone(tz).strftime("%H:%M")

    if sleep_time is None and wake_time is None:
        return "Not enough Telegram status data to determine sleep/wake times."

    return (
        f"Yesterday you went to sleep at {_fmt(sleep_time)} "
        f"and woke up at {_fmt(wake_time)} (telegram status)."
    )

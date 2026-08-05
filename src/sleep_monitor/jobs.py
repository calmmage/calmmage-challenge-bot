"""Scheduler jobs for the private sleep-monitor feature.

Two jobs registered when SLEEP_MONITOR_TARGET_ID is set:
  sleep_monitor_poll  — every N minutes, append status event to online_status_log
  sleep_monitor_report — daily at SLEEP_MONITOR_MORNING_HOUR, DM sleep/wake summary
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from botspot.utils import send_safe
from botspot.utils.deps_getters import get_database, get_scheduler
from loguru import logger

from src.sleep_monitor.analysis import find_sleep_wake, format_sleep_report
from src.sleep_monitor.config import SleepMonitorConfig
from src.sleep_monitor.store import append_event, ensure_index, events_in_range


# ---------------------------------------------------------------------------
# Telethon helpers (reuse pattern from service_account/jobs.py)
# ---------------------------------------------------------------------------


async def _get_client():
    from src.service_account.jobs import _any_authorized_client
    return await _any_authorized_client()


async def _fetch_status(user_id: int) -> tuple[bool, Optional[datetime]]:
    """Return (online, was_online_utc) for the target user."""
    client = await _get_client()
    if client is None:
        logger.debug("sleep_monitor: no authorized Telethon client, skipping poll")
        return False, None
    try:
        entity = await client.get_entity(user_id)
    except Exception as e:
        logger.debug(f"sleep_monitor: get_entity({user_id}) failed: {e}")
        return False, None

    status = getattr(entity, "status", None)
    if status is None:
        return False, None

    cls = status.__class__.__name__
    if cls == "UserStatusOnline":
        return True, None

    was_online = getattr(status, "was_online", None)
    if was_online is not None:
        # Normalise to UTC-aware
        if was_online.tzinfo is None:
            was_online = was_online.replace(tzinfo=timezone.utc)
        return False, was_online

    return False, None


# ---------------------------------------------------------------------------
# Poll job
# ---------------------------------------------------------------------------


async def _poll_target() -> None:
    cfg = SleepMonitorConfig()
    if not cfg.enabled:
        return

    assert cfg.sleep_monitor_target_id is not None
    user_id = cfg.sleep_monitor_target_id
    ts = datetime.now(timezone.utc)

    online, was_online = await _fetch_status(user_id)
    db = get_database()
    await append_event(db, user_id, ts, online, was_online)
    logger.debug(
        f"sleep_monitor: user={user_id} online={online} was_online={was_online}"
    )


# ---------------------------------------------------------------------------
# Morning report job
# ---------------------------------------------------------------------------


async def _morning_report() -> None:
    cfg = SleepMonitorConfig()
    if not cfg.enabled or cfg.report_chat_id is None:
        return

    assert cfg.sleep_monitor_target_id is not None
    db = get_database()
    now_utc = datetime.now(timezone.utc)

    # Look at roughly the last 18 hours — enough to cover last night + morning.
    since = now_utc - timedelta(hours=18)
    events = await events_in_range(db, cfg.sleep_monitor_target_id, since, now_utc)

    sleep_time, wake_time = find_sleep_wake(events)
    report = format_sleep_report(sleep_time, wake_time, cfg.sleep_monitor_morning_tz)

    # TODO (bonus): if the user sends a screenshot of a sleep-tracker app,
    # parse bedtime/wake via LLM vision (botspot LLMProvider or direct Anthropic
    # client) and append those numbers alongside the Telegram-derived ones.
    # Entry point: add a /sleep_screenshot command in a new router that accepts
    # a photo, calls client.messages.create(model="claude-opus-4-7",
    # messages=[{"role":"user","content":[{"type":"image",...},{"type":"text",
    # "text":"Extract sleep start and wake-up time from this screenshot."}]}]),
    # parses the response, and stores in a separate field in online_status_log
    # or a new collection.

    try:
        await send_safe(cfg.report_chat_id, report)
        logger.info(f"sleep_monitor: morning report sent to {cfg.report_chat_id}")
    except Exception as e:
        logger.warning(f"sleep_monitor: morning report send failed: {e}")


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


async def schedule_sleep_monitor() -> None:
    cfg = SleepMonitorConfig()
    if not cfg.enabled:
        logger.debug("sleep_monitor: SLEEP_MONITOR_TARGET_ID not set, skipping")
        return

    db = get_database()
    await ensure_index(db)

    scheduler = get_scheduler()

    scheduler.add_job(
        _poll_target,
        "interval",
        minutes=cfg.sleep_monitor_interval_minutes,
        id="sleep_monitor_poll",
        replace_existing=True,
    )

    scheduler.add_job(
        _morning_report,
        "cron",
        hour=cfg.sleep_monitor_morning_hour,
        minute=0,
        timezone=cfg.sleep_monitor_morning_tz,
        id="sleep_monitor_report",
        replace_existing=True,
    )

    logger.info(
        f"sleep_monitor: polling user {cfg.sleep_monitor_target_id} "
        f"every {cfg.sleep_monitor_interval_minutes} min; "
        f"report at {cfg.sleep_monitor_morning_hour}:00 {cfg.sleep_monitor_morning_tz}"
    )

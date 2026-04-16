"""Online-status polling using botspot's telethon_manager.

Re-uses whichever Telethon session any admin has authorized via /setup_telethon.
No custom session plumbing — treat telethon_manager as the source of truth.
"""

from datetime import datetime, timezone
from typing import Optional
from zoneinfo import ZoneInfo

from botspot.utils.deps_getters import get_scheduler, get_telethon_manager
from loguru import logger

from src.db import Repo
from src.time_utils import challenge_day_for


async def _any_authorized_client():
    mgr = get_telethon_manager()
    for client in mgr.clients.values():
        if client and await client.is_user_authorized():
            return client
    # Try reloading sessions from disk once, in case startup happened before auth.
    try:
        await mgr.init_all_sessions()
    except Exception as e:
        logger.debug(f"init_all_sessions fallback failed: {e}")
    for client in mgr.clients.values():
        if client and await client.is_user_authorized():
            return client
    return None


async def _last_seen_for(client, user_id: int) -> Optional[datetime]:
    try:
        entity = await client.get_entity(user_id)
    except Exception as e:
        logger.debug(f"get_entity({user_id}) failed: {e}")
        return None
    status = getattr(entity, "status", None)
    if status is None:
        return None
    cls = status.__class__.__name__
    if cls == "UserStatusOnline":
        return datetime.now(timezone.utc).replace(tzinfo=None)
    was_online = getattr(status, "was_online", None)
    if was_online:
        return was_online.replace(tzinfo=None) if was_online.tzinfo else was_online
    return None


async def _poll_online_status() -> None:
    from botspot.utils.deps_getters import get_database

    client = await _any_authorized_client()
    if client is None:
        logger.debug("No authorized Telethon client yet; skipping online poll")
        return

    repo = Repo(get_database())
    active = await repo.list_active_challenges()
    for challenge in active:
        assert challenge.id is not None
        users = await repo.active_users_for_challenge(challenge.id)
        for u in users:
            last = await _last_seen_for(client, u.user_id)
            if last is None:
                continue
            now_local = datetime.now(ZoneInfo(u.tz))
            day = challenge_day_for(now_local)
            await repo.set_online_seen(u.user_id, challenge.id, day, last)


async def schedule_online_polling() -> None:
    scheduler = get_scheduler()
    scheduler.add_job(
        _poll_online_status,
        "interval",
        minutes=15,
        id="online_status_poll",
        replace_existing=True,
    )
    logger.info("Online-status polling scheduled (every 15 min)")

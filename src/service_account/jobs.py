from datetime import datetime
from zoneinfo import ZoneInfo

from botspot.utils.deps_getters import get_scheduler
from loguru import logger

from src.db import Repo
from src.service_account.client import ServiceAccountClient
from src.time_utils import challenge_day_for


async def _poll_online_status() -> None:
    from botspot.utils.deps_getters import get_database

    from src.service_account.client import get_service_client

    client = get_service_client()
    if client is None:
        return

    repo = Repo(get_database())
    active = await repo.list_active_challenges()
    for challenge in active:
        assert challenge.id is not None
        users = await repo.active_users_for_challenge(challenge.id)
        for u in users:
            try:
                last = await client.get_last_seen(u.user_id)
            except Exception as e:
                logger.debug(f"last_seen failed user={u.user_id}: {e}")
                continue
            if last is None:
                continue
            now_local = datetime.now(ZoneInfo(u.tz))
            day = challenge_day_for(now_local)
            await repo.set_online_seen(u.user_id, challenge.id, day, last)


async def schedule_online_polling(repo: Repo, client: ServiceAccountClient) -> None:
    scheduler = get_scheduler()
    scheduler.add_job(
        _poll_online_status,
        "interval",
        minutes=15,
        id="service_account_online_poll",
        replace_existing=True,
    )
    logger.info("Service-account online polling scheduled (every 15 min)")

from datetime import datetime, time, timedelta
from typing import Optional
from zoneinfo import ZoneInfo

from botspot.utils import send_safe
from botspot.utils.deps_getters import get_scheduler
from loguru import logger

from src.db import Repo
from src.models import Challenge, ChallengeUser, SleepLog
from src.scoring import score_day, update_streak
from src.time_utils import CHALLENGE_DAY_PIVOT_HOUR, challenge_day_for


def _subtract_minutes(t: time, minutes: int) -> time:
    dt = datetime(2000, 1, 2, t.hour, t.minute) - timedelta(minutes=minutes)
    return dt.time()


async def _remind_bedtime(user_id: int, deadline_hhmm: str) -> None:
    try:
        await send_safe(
            user_id,
            f"⏰ Bedtime deadline in 30 min ({deadline_hhmm}). "
            "Send a message or 🎥 video note when you're in bed.",
        )
    except Exception as e:
        logger.warning(f"bed reminder to {user_id} failed: {e}")


async def _remind_wakeup(user_id: int, deadline_hhmm: str) -> None:
    try:
        await send_safe(user_id, f"⏰ Wake-up deadline in 30 min ({deadline_hhmm}).")
    except Exception as e:
        logger.warning(f"wake reminder to {user_id} failed: {e}")


async def _finalize_day_for_user(user_id: int, challenge_id) -> None:
    from botspot.utils.deps_getters import get_database

    repo = Repo(get_database())
    u = await repo.get_user(user_id, challenge_id)
    c = await repo.get_challenge(challenge_id)
    if not u or not c:
        return
    now_local = datetime.now(ZoneInfo(u.tz))
    day_to_finalize = challenge_day_for(now_local) - timedelta(days=1)
    log = await repo.get_log(user_id, challenge_id, day_to_finalize)
    if log is None:
        log = SleepLog(user_id=user_id, challenge_id=challenge_id, date=day_to_finalize)
    if log.finalized:
        return

    _ = c, u  # challenge/user retained in case future scoring needs their settings
    score = score_day(log)

    previous = await repo.recent_logs(user_id, challenge_id, limit=2)
    # recent_logs is sorted by date desc; we want yesterday-of-yesterday and current streak
    prev_streak = 0
    prev_score: Optional[float] = None
    for p in previous:
        if p.date < day_to_finalize:
            if prev_score is None:
                prev_score = p.score
                prev_streak = p.streak_after
            break

    new_streak = update_streak(prev_streak, score, prev_score)
    log.score = score
    log.streak_after = new_streak
    log.finalized = True
    await repo.upsert_log(log)


async def _daily_group_stats(challenge_id) -> None:
    from botspot.utils.deps_getters import get_database

    repo = Repo(get_database())
    c = await repo.get_challenge(challenge_id)
    if not c or not c.group_chat_id or c.status != "active":
        return
    users = await repo.active_users_for_challenge(challenge_id)
    if not users:
        return
    # summarize challenge-day that just finalized
    tz_hint = ZoneInfo(users[0].tz) if users else ZoneInfo("UTC")
    target_day = challenge_day_for(datetime.now(tz_hint)) - timedelta(days=1)
    ones = halves = zeros = 0
    for u in users:
        log = await repo.get_log(u.user_id, challenge_id, target_day)
        s = log.score if log else 0.0
        if s == 1.0:
            ones += 1
        elif s == 0.5:
            halves += 1
        else:
            zeros += 1
    await send_safe(
        c.group_chat_id,
        f"🌅 {c.name} · {target_day.isoformat()}\n"
        f"✅ {ones} on-time · ⚠️ {halves} half · ❌ {zeros} missed",
    )


async def _weekly_leaderboard(challenge_id) -> None:
    from botspot.utils.deps_getters import get_database, get_bot

    repo = Repo(get_database())
    c = await repo.get_challenge(challenge_id)
    if not c or not c.group_chat_id or c.status != "active":
        return
    users = await repo.active_users_for_challenge(challenge_id)
    if not users:
        return
    rows: list[tuple[int, int, float, datetime]] = []
    bot = get_bot()
    for u in users:
        logs = await repo.recent_logs(u.user_id, challenge_id, limit=7)
        streak = logs[0].streak_after if logs else 0
        total = sum(log.score for log in logs)
        rows.append((u.user_id, streak, total, u.joined_at))
    rows.sort(key=lambda r: (-r[2], -r[1], r[3]))
    lines = [f"🏆 Weekly leaderboard · {c.name}"]
    for rank, (uid, streak, total, _) in enumerate(rows, 1):
        try:
            member = await bot.get_chat(uid)
            name = member.first_name or member.username or str(uid)
        except Exception:
            name = str(uid)
        lines.append(f"{rank}. {name} — {total:.1f} pts · streak {streak}")
    await send_safe(c.group_chat_id, "\n".join(lines))


async def schedule_user_jobs(user: ChallengeUser) -> None:
    scheduler = get_scheduler()
    bed_remind = _subtract_minutes(user.bedtime_deadline, 30)
    wake_remind = _subtract_minutes(user.wakeup_deadline, 30)

    scheduler.add_job(
        _remind_bedtime,
        "cron",
        hour=bed_remind.hour,
        minute=bed_remind.minute,
        timezone=user.tz,
        args=[user.user_id, user.bedtime_deadline.strftime("%H:%M")],
        id=f"bed_remind_{user.user_id}_{user.challenge_id}",
        replace_existing=True,
    )
    scheduler.add_job(
        _remind_wakeup,
        "cron",
        hour=wake_remind.hour,
        minute=wake_remind.minute,
        timezone=user.tz,
        args=[user.user_id, user.wakeup_deadline.strftime("%H:%M")],
        id=f"wake_remind_{user.user_id}_{user.challenge_id}",
        replace_existing=True,
    )
    scheduler.add_job(
        _finalize_day_for_user,
        "cron",
        hour=CHALLENGE_DAY_PIVOT_HOUR,
        minute=5,
        timezone=user.tz,
        args=[user.user_id, user.challenge_id],
        id=f"finalize_{user.user_id}_{user.challenge_id}",
        replace_existing=True,
    )


async def schedule_challenge_jobs(
    challenge: Challenge, users: list[ChallengeUser]
) -> None:
    scheduler = get_scheduler()
    tz = ZoneInfo(users[0].tz) if users else ZoneInfo("UTC")
    scheduler.add_job(
        _daily_group_stats,
        "cron",
        hour=8,
        minute=0,
        timezone=str(tz),
        args=[challenge.id],
        id=f"daily_stats_{challenge.id}",
        replace_existing=True,
    )
    scheduler.add_job(
        _weekly_leaderboard,
        "cron",
        day_of_week="sun",
        hour=20,
        minute=0,
        timezone=str(tz),
        args=[challenge.id],
        id=f"weekly_leaderboard_{challenge.id}",
        replace_existing=True,
    )


async def schedule_all_jobs(repo: Repo) -> None:
    active = await repo.list_active_challenges()
    for challenge in active:
        assert challenge.id is not None
        users = await repo.active_users_for_challenge(challenge.id)
        for u in users:
            try:
                await schedule_user_jobs(u)
            except Exception as e:
                logger.warning(f"schedule user {u.user_id} failed: {e}")
        try:
            await schedule_challenge_jobs(challenge, users)
        except Exception as e:
            logger.warning(f"schedule challenge {challenge.code} failed: {e}")

    try:
        from src.service_account.jobs import schedule_online_polling

        await schedule_online_polling()
    except Exception as e:
        logger.warning(f"schedule online polling failed: {e}")

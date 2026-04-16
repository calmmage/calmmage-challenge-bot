from datetime import datetime, time
from zoneinfo import ZoneInfo

from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from botspot import commands_menu
from botspot.utils import send_safe

from src.db import Repo
from src.setup_flows import validate_tightening
from src.time_utils import challenge_day_for

router = Router(name="settings")
router.message.filter(F.chat.type == "private")


def _parse_hhmm(s: str) -> time | None:
    try:
        hh, mm = (int(x) for x in s.strip().split(":"))
        return time(hh, mm)
    except Exception:
        return None


@commands_menu.botspot_command("tighten_bed", "Move bedtime deadline earlier")
@router.message(Command("tighten_bed"))
async def tighten_bed(message: Message, command: CommandObject, repo: Repo) -> None:
    assert message.from_user
    new_time = _parse_hhmm(command.args or "")
    if not new_time:
        await send_safe(message.chat.id, "Usage: /tighten_bed HH:MM")
        return
    memberships = await repo.active_memberships_for_user(message.from_user.id)
    if not memberships:
        await send_safe(message.chat.id, "You're not in any active challenge.")
        return
    m = memberships[0]
    if not validate_tightening(m.bedtime_deadline, new_time):
        await send_safe(
            message.chat.id,
            f"Deadlines can only be tightened, never relaxed. "
            f"Current: {m.bedtime_deadline.strftime('%H:%M')}.",
        )
        return
    m.bedtime_deadline = new_time
    await repo.save_user(m)
    await send_safe(
        message.chat.id, f"Bedtime deadline now {new_time.strftime('%H:%M')}."
    )


@commands_menu.botspot_command("tighten_wake", "Move wake deadline earlier")
@router.message(Command("tighten_wake"))
async def tighten_wake(message: Message, command: CommandObject, repo: Repo) -> None:
    assert message.from_user
    new_time = _parse_hhmm(command.args or "")
    if not new_time:
        await send_safe(message.chat.id, "Usage: /tighten_wake HH:MM")
        return
    memberships = await repo.active_memberships_for_user(message.from_user.id)
    if not memberships:
        await send_safe(message.chat.id, "You're not in any active challenge.")
        return
    m = memberships[0]
    if not validate_tightening(m.wakeup_deadline, new_time):
        await send_safe(
            message.chat.id,
            f"Deadlines can only be tightened, never relaxed. "
            f"Current: {m.wakeup_deadline.strftime('%H:%M')}.",
        )
        return
    m.wakeup_deadline = new_time
    await repo.save_user(m)
    await send_safe(message.chat.id, f"Wake deadline now {new_time.strftime('%H:%M')}.")


@commands_menu.botspot_command("status", "Today's log and streak")
@router.message(Command("status"))
async def status(message: Message, repo: Repo) -> None:
    assert message.from_user
    memberships = await repo.active_memberships_for_user(message.from_user.id)
    if not memberships:
        await send_safe(message.chat.id, "You're not in any active challenge.")
        return
    m = memberships[0]
    now_local = datetime.now(ZoneInfo(m.tz))
    day = challenge_day_for(now_local)
    assert m.challenge_id is not None
    log = await repo.get_log(message.from_user.id, m.challenge_id, day)
    recent = await repo.recent_logs(message.from_user.id, m.challenge_id, limit=1)
    streak = recent[0].streak_after if recent and recent[0].finalized else 0

    def _fmt(ci) -> str:
        if ci is None:
            return "—"
        return f"{ci.ts.strftime('%H:%M UTC')} ({'✅' if ci.on_time else '⚠️'})"

    bed = _fmt(log.bed) if log else "—"
    wake = _fmt(log.wake) if log else "—"
    online = (
        log.online_last_seen.strftime("%H:%M UTC")
        if log and log.online_last_seen
        else "—"
    )

    await send_safe(
        message.chat.id,
        f"<b>Today</b> ({day.isoformat()})\n"
        f"Bed: {bed}\nWake: {wake}\n"
        f"Seen online: {online}\n"
        f"Bedtime deadline: {m.bedtime_deadline.strftime('%H:%M')} · "
        f"Wake deadline: {m.wakeup_deadline.strftime('%H:%M')}\n"
        f"Streak: <b>{streak}</b>",
    )


@commands_menu.botspot_command("history", "Last 14 days")
@router.message(Command("history"))
async def history(message: Message, repo: Repo) -> None:
    assert message.from_user
    memberships = await repo.active_memberships_for_user(message.from_user.id)
    if not memberships:
        await send_safe(message.chat.id, "You're not in any active challenge.")
        return
    m = memberships[0]
    assert m.challenge_id is not None
    logs = await repo.recent_logs(message.from_user.id, m.challenge_id, limit=14)
    if not logs:
        await send_safe(message.chat.id, "No logs yet.")
        return
    lines = []
    for log in logs:
        mark = {1.0: "✅", 0.5: "⚠️", 0.0: "❌"}.get(log.score, "·")
        lines.append(f"{log.date.isoformat()} {mark} streak={log.streak_after}")
    await send_safe(message.chat.id, "\n".join(lines))


@commands_menu.botspot_command(
    "how_to_share_online", "Instructions for the online-status bonus"
)
@router.message(Command("how_to_share_online"))
async def how_to_share_online(message: Message) -> None:
    await send_safe(
        message.chat.id,
        "<b>Bonus: share your online status</b>\n\n"
        "1. Add the challenge service account to your Telegram contacts "
        "(phone +41 77 218 4188).\n"
        "2. Telegram → Settings → Privacy &amp; Security → Last Seen &amp; Online → "
        "My Contacts (or add a specific exception).\n"
        "3. I'll use 'last seen' as a fallback hint in /status.\n\n"
        "Skip if you'd rather not — scoring still works off your видео-заметки.",
    )

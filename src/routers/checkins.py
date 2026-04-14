from datetime import datetime, time
from zoneinfo import ZoneInfo

from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from botspot import commands_menu
from botspot.utils import send_safe

from src.db import Repo
from src.models import ChallengeUser, CheckIn, ProofKind, ProofPolicy, UserProofChoice
from src.scoring import _effective_policy, _proof_ok
from src.setup_flows import validate_tightening
from src.time_utils import bed_on_time, challenge_day_for, in_bed_window, in_wake_window

router = Router(name="checkins")
router.message.filter(F.chat.type == "private")


def _proof_kind(message: Message) -> ProofKind | None:
    if message.video_note is not None:
        return "video_note"
    if message.text is not None and not message.text.startswith("/"):
        return "text"
    return None


async def _resolve_active_membership(
    user_id: int, repo: Repo
) -> tuple[ChallengeUser, datetime] | None:
    memberships = await repo.active_memberships_for_user(user_id)
    if not memberships:
        return None
    membership = memberships[0]
    now_local = datetime.now(ZoneInfo(membership.tz))
    return membership, now_local


def _effective_user_choice(
    policy: ProofPolicy, choice: UserProofChoice | None
) -> UserProofChoice:
    return _effective_policy(policy, choice)


async def _handle_checkin(message: Message, repo: Repo, kind: ProofKind) -> None:
    assert message.from_user
    ctx = await _resolve_active_membership(message.from_user.id, repo)
    if ctx is None:
        return
    membership, now_local = ctx
    challenge = await repo.get_challenge(membership.challenge_id)
    if not challenge or challenge.status != "active":
        return

    if in_bed_window(now_local):
        field = "bed"
        deadline: time = membership.bedtime_deadline
        policy = challenge.bed_proof_policy
        user_choice = membership.bed_proof_choice
    elif in_wake_window(now_local):
        field = "wake"
        deadline = membership.wakeup_deadline
        policy = challenge.wake_proof_policy
        user_choice = membership.wake_proof_choice
    else:
        return  # silent — outside any window

    effective = _effective_user_choice(policy, user_choice)
    if not _proof_ok(kind, effective):
        await message.reply("🎥 Video note required for this one.")
        return

    on_time = bed_on_time(now_local, deadline)
    day = challenge_day_for(now_local)
    check_in = CheckIn(ts=now_local.astimezone(ZoneInfo("UTC")).replace(tzinfo=None), kind=kind, on_time=on_time)
    assert challenge.id is not None
    existing = await repo.get_log(message.from_user.id, challenge.id, day)
    if existing and getattr(existing, field) is not None:
        await message.reply(f"Already logged your {field} for today ({getattr(existing, field).ts.strftime('%H:%M')}).")
        return
    await repo.set_check_in(message.from_user.id, challenge.id, day, field, check_in)

    tag = "✅ on time" if on_time else "⚠️ late"
    await message.reply(f"Logged {field} · {tag}")


@router.message(F.video_note)
async def video_note_handler(message: Message, repo: Repo) -> None:
    await _handle_checkin(message, repo, "video_note")


@router.message(F.text, ~F.text.startswith("/"))
async def text_handler(message: Message, repo: Repo) -> None:
    await _handle_checkin(message, repo, "text")


@commands_menu.botspot_command("tighten_bed", "Move bedtime deadline earlier")
@router.message(Command("tighten_bed"))
async def tighten_bed(
    message: Message, command: CommandObject, repo: Repo
) -> None:
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
            f"Deadlines can only be tightened, never relaxed. Current: {m.bedtime_deadline.strftime('%H:%M')}.",
        )
        return
    m.bedtime_deadline = new_time
    await repo.save_user(m)
    await send_safe(message.chat.id, f"Bedtime deadline now {new_time.strftime('%H:%M')}.")


@commands_menu.botspot_command("tighten_wake", "Move wake deadline earlier")
@router.message(Command("tighten_wake"))
async def tighten_wake(
    message: Message, command: CommandObject, repo: Repo
) -> None:
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
            f"Deadlines can only be tightened, never relaxed. Current: {m.wakeup_deadline.strftime('%H:%M')}.",
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

    bed = f"{log.bed.ts.strftime('%H:%MZ')} ({'✅' if log.bed.on_time else '⚠️'})" if log and log.bed else "—"
    wake = f"{log.wake.ts.strftime('%H:%MZ')} ({'✅' if log.wake.on_time else '⚠️'})" if log and log.wake else "—"
    await send_safe(
        message.chat.id,
        f"<b>Today</b> ({day.isoformat()})\n"
        f"Bed: {bed}\nWake: {wake}\n"
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


def _parse_hhmm(s: str) -> time | None:
    try:
        hh, mm = (int(x) for x in s.strip().split(":"))
        return time(hh, mm)
    except Exception:
        return None


@commands_menu.botspot_command(
    "how_to_share_online", "Instructions for the online-status bonus"
)
@router.message(Command("how_to_share_online"))
async def how_to_share_online(message: Message) -> None:
    await send_safe(
        message.chat.id,
        "<b>Bonus: share your online status</b>\n\n"
        "1. Add the challenge service account to your Telegram contacts (phone +41 77 218 4188).\n"
        "2. Telegram → Settings → Privacy &amp; Security → Last Seen &amp; Online → My Contacts "
        "(or add a specific exception allowing the service account).\n"
        "3. That's it — I'll see when you were last online and use it as a fallback signal.\n\n"
        "If you'd rather not, ignore this — scoring still works off your messages.",
    )

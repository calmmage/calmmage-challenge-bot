"""Setup wizard for a participant.

Exposes `run_setup_wizard(...)` so the group router can kick it off after /join
in a group; also keeps a DM-side /join <code> as a fallback.
"""

from datetime import datetime, time

from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from botspot import commands_menu
from botspot.components.features.user_interactions import ask_user, ask_user_choice
from botspot.utils import send_safe

from src.db import Repo
from src.models import Challenge, ChallengeUser
from src.setup_flows import deadline_from_usual, defaults
from src.time_utils import infer_tz_from_offset, is_valid_tz

router = Router(name="registration")
router.message.filter(F.chat.type == "private")


def _parse_hhmm(s: str) -> time | None:
    try:
        hh, mm = (int(x) for x in s.strip().split(":"))
        return time(hh, mm)
    except Exception:
        return None


async def _ask_timezone(chat_id: int, state: FSMContext) -> str | None:
    method = await ask_user_choice(
        chat_id,
        "How should I figure out your timezone?",
        {
            "current": "🕐 Send current local time",
            "manual": "✏️ Type Olson name (e.g. Europe/Zurich)",
        },
        state,
    )
    if method == "current":
        raw = await ask_user(chat_id, "Your current local time as HH:MM:", state)
        if not raw:
            return None
        tz = infer_tz_from_offset(raw)
        if tz:
            await send_safe(chat_id, f"Inferred timezone: <code>{tz}</code>")
            return tz
        await send_safe(chat_id, "Could not infer timezone from that.")
        return None
    if method == "manual":
        raw = await ask_user(chat_id, "Enter Olson name, e.g. Europe/Zurich:", state)
        if raw and is_valid_tz(raw.strip()):
            return raw.strip()
        await send_safe(chat_id, "That's not a known timezone.")
        return None
    return None


async def _manual_flow(chat_id: int, state: FSMContext) -> tuple[time, time] | None:
    bed_raw = await ask_user(chat_id, "Bedtime deadline (HH:MM local):", state)
    bed = _parse_hhmm(bed_raw or "")
    wake_raw = await ask_user(chat_id, "Wake-up deadline (HH:MM local):", state)
    wake = _parse_hhmm(wake_raw or "")
    if not bed or not wake:
        await send_safe(chat_id, "Couldn't parse those.")
        return None
    return bed, wake


async def _guided_flow(
    chat_id: int, state: FSMContext
) -> tuple[tuple[time, time] | None, time | None, time | None]:
    """Returns (deadlines, usual_bed, usual_wake)."""
    bed_raw = await ask_user(
        chat_id,
        "What time do you usually go to bed lately (HH:MM)? "
        "Reply <code>varies</code> if it's all over the place.",
        state,
    )
    if bed_raw and bed_raw.strip().lower() in ("varies", "different", "varied"):
        await send_safe(
            chat_id, "Using sensible midnight-ish defaults (bed 23:30, wake 07:30)."
        )
        return defaults(), None, None
    usual_bed = _parse_hhmm(bed_raw or "")
    wake_raw = await ask_user(chat_id, "And your usual wake-up time (HH:MM)?", state)
    usual_wake = _parse_hhmm(wake_raw or "")
    if not usual_bed or not usual_wake:
        await send_safe(chat_id, "Couldn't parse that. Aborting.")
        return None, None, None
    difficulty = await ask_user_choice(
        chat_id,
        "How much earlier should your deadline be?",
        {
            "light": "Light (−30 min)",
            "medium": "Medium (−1h) ⭐ recommended",
            "hard": "Hard (−2h)",
            "manual": "Manual",
        },
        state,
        default_choice="medium",
    )
    if difficulty == "manual":
        return await _manual_flow(chat_id, state), usual_bed, usual_wake
    if difficulty in ("light", "medium", "hard"):
        return (
            (
                deadline_from_usual(usual_bed, difficulty),  # type: ignore[arg-type]
                deadline_from_usual(usual_wake, difficulty),  # type: ignore[arg-type]
            ),
            usual_bed,
            usual_wake,
        )
    return None, usual_bed, usual_wake


async def run_setup_wizard(
    user_id: int,
    challenge: Challenge,
    state: FSMContext,
    repo: Repo,
) -> ChallengeUser | None:
    """Run the DM-side wizard for a user joining `challenge`. Returns the saved
    ChallengeUser, or None on abort."""
    assert challenge.id is not None
    chat_id = user_id  # DM chat id == user id

    existing = await repo.get_user(user_id, challenge.id)
    if existing and existing.active:
        await send_safe(chat_id, "You're already registered in this challenge.")
        return existing

    tz = await _ask_timezone(chat_id, state)
    if not tz:
        return None

    flow = await ask_user_choice(
        chat_id,
        "How do you want to set your deadlines?",
        {
            "guided": "Guided (recommended)",
            "manual": "Manual — I know my times",
            "defaults": "Use sensible defaults (23:30 / 07:30)",
        },
        state,
        default_choice="guided",
    )

    result: tuple[time, time] | None = None
    usual_bed: time | None = None
    usual_wake: time | None = None
    if flow == "manual":
        result = await _manual_flow(chat_id, state)
    elif flow == "defaults":
        result = defaults()
    else:
        flow = "guided"
        result, usual_bed, usual_wake = await _guided_flow(chat_id, state)

    if not result:
        return None
    bed_deadline, wake_deadline = result

    user = ChallengeUser(
        user_id=user_id,
        challenge_id=challenge.id,
        tz=tz,
        bedtime_deadline=bed_deadline,
        wakeup_deadline=wake_deadline,
        usual_bedtime=usual_bed,
        usual_wakeup=usual_wake,
        setup_flow=flow,  # type: ignore[arg-type]
        joined_at=datetime.utcnow(),
        active=True,
    )
    await repo.save_user(user)

    from src.scheduler_jobs import schedule_user_jobs

    try:
        await schedule_user_jobs(user)
    except Exception as e:
        from loguru import logger

        logger.warning(f"Could not schedule user jobs: {e}")

    await send_safe(
        chat_id,
        "🎯 You're in.\n"
        f"Timezone: <code>{tz}</code>\n"
        f"Bedtime deadline: <b>{bed_deadline.strftime('%H:%M')}</b>\n"
        f"Wake-up deadline: <b>{wake_deadline.strftime('%H:%M')}</b>\n\n"
        "Now send 🎥 <b>video notes</b> (кружочки) in the challenge group — "
        "one when you're in bed, one when you wake up. "
        "Use /tighten_bed or /tighten_wake to move a deadline earlier.",
    )
    return user


# No @botspot_command here — the group router owns the /join menu entry.
# This handler is a silent DM-side fallback for deep-link re-entries.
@router.message(Command("join"))
async def join_in_dm(
    message: Message, command: CommandObject, state: FSMContext, repo: Repo
) -> None:
    """DM-side fallback — the normal flow is /join in the group."""
    assert message.from_user
    code = (command.args or "").strip()
    if not code:
        await send_safe(
            message.chat.id,
            "Usage: /join &lt;challenge_code&gt;\n"
            "Normally you'd type this in the challenge group — this is the fallback.",
        )
        return
    challenge = await repo.get_challenge_by_code(code)
    if not challenge or challenge.status != "active":
        await send_safe(
            message.chat.id, f"No active challenge with code <code>{code}</code>."
        )
        return
    await run_setup_wizard(message.from_user.id, challenge, state, repo)

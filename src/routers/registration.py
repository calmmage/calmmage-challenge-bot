from datetime import datetime, time

from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from botspot import commands_menu
from botspot.components.features.user_interactions import ask_user, ask_user_choice
from botspot.utils import send_safe

from src.db import Repo
from src.models import ChallengeUser, UserProofChoice
from src.setup_flows import (
    DEFAULT_BEDTIME,
    DEFAULT_WAKEUP,
    deadline_from_usual,
    defaults,
)
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
            "geo": "📍 Send location",
            "current": "🕐 Send current local time",
            "manual": "✏️ Type Olson name (e.g. Europe/Zurich)",
        },
        state,
    )
    if method == "geo":
        await send_safe(chat_id, "Attach a location (paperclip → Location) and send it here.")
        raw = await ask_user(chat_id, "Waiting for location…", state, timeout=180.0)
        # ask_user returns text; location is handled separately below.
        # If user sent text instead, try to parse as Olson name.
        if raw and is_valid_tz(raw.strip()):
            return raw.strip()
        await send_safe(chat_id, "Couldn't read a location. Try again with /join.")
        return None
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


async def _guided_flow(chat_id: int, state: FSMContext) -> tuple[time, time] | None:
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
        return DEFAULT_BEDTIME, DEFAULT_WAKEUP
    usual_bed = _parse_hhmm(bed_raw or "")
    if not usual_bed:
        await send_safe(chat_id, "Couldn't parse that time.")
        return None

    wake_raw = await ask_user(chat_id, "And your usual wake-up time (HH:MM)?", state)
    usual_wake = _parse_hhmm(wake_raw or "")
    if not usual_wake:
        await send_safe(chat_id, "Couldn't parse that time.")
        return None

    difficulty = await ask_user_choice(
        chat_id,
        "How much earlier should your deadline be vs. that usual time?",
        {
            "light": "Light (−30 min)",
            "medium": "Medium (−1h) ⭐ recommended",
            "hard": "Hard (−2h)",
            "manual": "Manual — I'll type deadlines",
        },
        state,
        default_choice="medium",
    )
    if difficulty == "manual":
        return await _manual_flow(chat_id, state)
    if difficulty in ("light", "medium", "hard"):
        bed_deadline = deadline_from_usual(usual_bed, difficulty)  # type: ignore[arg-type]
        wake_deadline = deadline_from_usual(usual_wake, difficulty)  # type: ignore[arg-type]
        return bed_deadline, wake_deadline
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


async def _ask_user_proof(chat_id: int, state: FSMContext, which: str) -> UserProofChoice:
    choice = await ask_user_choice(
        chat_id,
        f"Proof for {which}: what do you want to be held to?",
        {"text_or_video": "Text or video note", "video_only": "Video note only"},
        state,
        default_choice="text_or_video",
    )
    return choice if choice in ("text_or_video", "video_only") else "text_or_video"  # type: ignore[return-value]


@commands_menu.botspot_command("join", "Join an active challenge")
@router.message(Command("join"))
async def join_challenge(
    message: Message, command: CommandObject, state: FSMContext, repo: Repo
) -> None:
    assert message.from_user
    code = (command.args or "").strip()
    chat_id = message.chat.id
    if not code:
        await send_safe(chat_id, "Usage: /join &lt;challenge_code&gt;")
        return
    challenge = await repo.get_challenge_by_code(code)
    if not challenge or challenge.status != "active":
        await send_safe(chat_id, f"No active challenge with code <code>{code}</code>.")
        return
    assert challenge.id is not None
    existing = await repo.get_user(message.from_user.id, challenge.id)
    if existing and existing.active:
        await send_safe(chat_id, "You're already registered in this challenge.")
        return

    tz = await _ask_timezone(chat_id, state)
    if not tz:
        return

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
        # Capture usuals in the guided flow for display
        bed_raw = await ask_user(
            chat_id,
            "What time do you usually go to bed lately (HH:MM)? "
            "Reply <code>varies</code> if it's all over the place.",
            state,
        )
        if bed_raw and bed_raw.strip().lower() in ("varies", "different", "varied"):
            result = defaults()
        else:
            usual_bed = _parse_hhmm(bed_raw or "")
            wake_raw = await ask_user(
                chat_id, "And your usual wake-up time (HH:MM)?", state
            )
            usual_wake = _parse_hhmm(wake_raw or "")
            if not usual_bed or not usual_wake:
                await send_safe(chat_id, "Couldn't parse that. Aborting.")
                return
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
                result = await _manual_flow(chat_id, state)
            elif difficulty in ("light", "medium", "hard"):
                result = (
                    deadline_from_usual(usual_bed, difficulty),  # type: ignore[arg-type]
                    deadline_from_usual(usual_wake, difficulty),  # type: ignore[arg-type]
                )
    if not result:
        return
    bed_deadline, wake_deadline = result

    bed_choice: UserProofChoice | None = None
    wake_choice: UserProofChoice | None = None
    if challenge.bed_proof_policy == "user_choice":
        bed_choice = await _ask_user_proof(chat_id, state, "bedtime")
    if challenge.wake_proof_policy == "user_choice":
        wake_choice = await _ask_user_proof(chat_id, state, "wake-up")

    user = ChallengeUser(
        user_id=message.from_user.id,
        challenge_id=challenge.id,
        tz=tz,
        bedtime_deadline=bed_deadline,
        wakeup_deadline=wake_deadline,
        bed_proof_choice=bed_choice,
        wake_proof_choice=wake_choice,
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
        "Every evening send me a message or 🎥 video note when you're in bed. "
        "Every morning do the same when you wake up.\n"
        "Use /tighten_bed or /tighten_wake to move a deadline earlier (never later).",
    )

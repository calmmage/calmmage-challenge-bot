"""Setup wizard for a participant.

Exposes `run_setup_wizard(...)` so the group router can kick it off after /join
in a group; also keeps a DM-side /join <code> as a fallback.
"""

from datetime import datetime, time

from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from botspot.components.features.user_interactions import ask_user, ask_user_choice
from botspot.i18n import get_lang, t
from botspot.utils import send_safe
from loguru import logger

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
        t("ask_tz_method"),
        {
            "current": t("ask_tz_current"),
            "manual": t("ask_tz_manual"),
        },
        state,
    )
    if method == "current":
        raw = await ask_user(chat_id, t("ask_tz_current_prompt"), state)
        if not raw:
            return None
        tz = infer_tz_from_offset(raw)
        if tz:
            await send_safe(chat_id, t("tz_inferred", tz=tz))
            return tz
        await send_safe(chat_id, t("tz_infer_failed"))
        return None
    if method == "manual":
        raw = await ask_user(chat_id, t("ask_tz_olson_prompt"), state)
        if raw and is_valid_tz(raw.strip()):
            return raw.strip()
        await send_safe(chat_id, t("tz_unknown"))
        return None
    return None


async def _manual_flow(chat_id: int, state: FSMContext) -> tuple[time, time] | None:
    bed_raw = await ask_user(chat_id, t("ask_bed_manual"), state)
    bed = _parse_hhmm(bed_raw or "")
    wake_raw = await ask_user(chat_id, t("ask_wake_manual"), state)
    wake = _parse_hhmm(wake_raw or "")
    if not bed or not wake:
        await send_safe(chat_id, t("parse_failed"))
        return None
    return bed, wake


async def _guided_flow(
    chat_id: int, state: FSMContext
) -> tuple[tuple[time, time] | None, time | None, time | None]:
    """Returns (deadlines, usual_bed, usual_wake)."""
    bed_raw = await ask_user(chat_id, t("ask_usual_bed"), state)
    if bed_raw and bed_raw.strip().lower() in ("varies", "different", "varied"):
        await send_safe(chat_id, t("usual_varies_defaults"))
        return defaults(), None, None
    usual_bed = _parse_hhmm(bed_raw or "")
    wake_raw = await ask_user(chat_id, t("ask_usual_wake"), state)
    usual_wake = _parse_hhmm(wake_raw or "")
    if not usual_bed or not usual_wake:
        await send_safe(chat_id, t("parse_failed_abort"))
        return None, None, None
    difficulty = await ask_user_choice(
        chat_id,
        t("ask_difficulty"),
        {
            "light": t("difficulty_light"),
            "medium": t("difficulty_medium"),
            "hard": t("difficulty_hard"),
            "manual": t("difficulty_manual"),
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
        await send_safe(chat_id, t("already_registered"))
        return existing

    tz = await _ask_timezone(chat_id, state)
    if not tz:
        return None

    flow = await ask_user_choice(
        chat_id,
        t("ask_flow"),
        {
            "guided": t("flow_guided"),
            "manual": t("flow_manual"),
            "defaults": t("flow_defaults"),
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
        lang=get_lang(),
        joined_at=datetime.utcnow(),
        active=True,
    )
    await repo.save_user(user)

    from src.scheduler_jobs import schedule_user_jobs

    try:
        await schedule_user_jobs(user)
    except Exception as e:
        logger.warning(f"Could not schedule user jobs: {e}")

    await send_safe(
        chat_id,
        t(
            "wizard_done",
            tz=tz,
            bed=bed_deadline.strftime("%H:%M"),
            wake=wake_deadline.strftime("%H:%M"),
        ),
    )
    return user


async def _challenges_user_can_join(
    bot, repo: Repo, user_id: int
) -> list[Challenge]:
    """Active challenges whose bound group the user is actually a member of."""
    available: list[Challenge] = []
    for c in await repo.list_active_challenges():
        if not c.group_chat_id:
            continue
        try:
            member = await bot.get_chat_member(c.group_chat_id, user_id)
        except Exception as e:
            logger.debug(f"get_chat_member failed for {c.code}: {e}")
            continue
        if member.status in ("left", "kicked"):
            continue
        available.append(c)
    return available


# No @botspot_command here — the group router owns the /join menu entry.
# This handler is a silent DM-side fallback for deep-link re-entries.
@router.message(Command("join"))
async def join_in_dm(
    message: Message, command: CommandObject, state: FSMContext, repo: Repo
) -> None:
    """DM-side /join — with code, joins directly; without, shows buttons."""
    assert message.from_user
    assert message.bot is not None
    code = (command.args or "").strip()
    if code:
        challenge = await repo.get_challenge_by_code(code)
        if not challenge or challenge.status != "active":
            await send_safe(
                message.chat.id, t("join_no_challenge_with_code", code=code)
            )
            return
        await run_setup_wizard(message.from_user.id, challenge, state, repo)
        return

    available = await _challenges_user_can_join(
        message.bot, repo, message.from_user.id
    )
    if not available:
        await send_safe(message.chat.id, t("join_no_group_member"))
        return

    rows = [
        [
            InlineKeyboardButton(
                text=t("join_button", name=c.name),
                callback_data=f"join:{c.code}",
            )
        ]
        for c in available
    ]
    kb = InlineKeyboardMarkup(inline_keyboard=rows)
    await send_safe(message.chat.id, t("join_pick"), reply_markup=kb)


@router.callback_query(lambda c: c.data and c.data.startswith("join:"))
async def join_callback(
    callback: CallbackQuery, state: FSMContext, repo: Repo
) -> None:
    assert callback.data
    assert callback.from_user
    code = callback.data.split(":", 1)[1]
    challenge = await repo.get_challenge_by_code(code)
    if not challenge or challenge.status != "active":
        await callback.answer(
            t("join_no_active_callback", code=code), show_alert=True
        )
        return
    await callback.answer()
    if callback.message is not None:
        try:
            await callback.message.edit_text(
                t("join_starting_setup", name=challenge.name, code=challenge.code),
                parse_mode="HTML",
            )
        except Exception as e:
            logger.debug(f"edit_text failed: {e}")
    await run_setup_wizard(callback.from_user.id, challenge, state, repo)

from datetime import date, datetime, timedelta

from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from botspot import commands_menu
from botspot.components.features.user_interactions import ask_user, ask_user_choice
from botspot.utils import send_safe
from botspot.utils.admin_filter import AdminFilter
from loguru import logger

from src.db import Repo
from src.models import Challenge

router = Router(name="admin")
router.message.filter(AdminFilter())
router.callback_query.filter(AdminFilter())


def _parse_date(s: str) -> date | None:
    try:
        return date.fromisoformat(s.strip())
    except ValueError:
        return None


async def _ask_start_date(chat_id: int, state: FSMContext) -> date | None:
    today = date.today()
    choice = await ask_user_choice(
        chat_id,
        "Start date?",
        {
            "today": f"Today ({today.isoformat()})",
            "tomorrow": f"Tomorrow ({(today + timedelta(days=1)).isoformat()})",
            "custom": "Custom date (YYYY-MM-DD)",
        },
        state,
        default_choice="today",
    )
    if choice == "today":
        return today
    if choice == "tomorrow":
        return today + timedelta(days=1)
    raw = await ask_user(chat_id, "Enter start date (YYYY-MM-DD):", state)
    return _parse_date(raw or "") or today


async def _ask_end_date(chat_id: int, state: FSMContext, starts_at: date) -> date | None:
    choice = await ask_user_choice(
        chat_id,
        "End date?",
        {
            "1w": f"1 week ({(starts_at + timedelta(weeks=1)).isoformat()})",
            "2w": f"2 weeks ({(starts_at + timedelta(weeks=2)).isoformat()})",
            "3w": f"3 weeks ({(starts_at + timedelta(weeks=3)).isoformat()})",
            "custom": "Custom date",
            "none": "No end date",
        },
        state,
        default_choice="2w",
    )
    if choice == "1w":
        return starts_at + timedelta(weeks=1)
    if choice == "2w":
        return starts_at + timedelta(weeks=2)
    if choice == "3w":
        return starts_at + timedelta(weeks=3)
    if choice == "none":
        return None
    raw = await ask_user(chat_id, "Enter end date (YYYY-MM-DD):", state)
    return _parse_date(raw or "")


@commands_menu.botspot_command("admin_new_challenge", "Create a new challenge (admin)")
@router.message(Command("admin_new_challenge"))
async def new_challenge(message: Message, state: FSMContext, repo: Repo) -> None:
    assert message.from_user
    chat_id = message.chat.id

    code = await ask_user(
        chat_id, "Challenge code (short, unique, e.g. sleep-apr26):", state
    )
    if not code:
        return
    code = code.strip()
    if await repo.get_challenge_by_code(code):
        await send_safe(chat_id, f"Code <code>{code}</code> already exists.")
        return

    name = await ask_user(chat_id, "Human-readable name:", state) or code

    starts_at = await _ask_start_date(chat_id, state)
    assert starts_at is not None
    ends_at = await _ask_end_date(chat_id, state, starts_at)

    # v2: always video-only. Policy fields are kept on the model for future flex.
    challenge = Challenge(
        code=code,
        name=name,
        created_by=message.from_user.id,
        created_at=datetime.utcnow(),
        starts_at=starts_at,
        ends_at=ends_at,
        bed_proof_policy="video_only",
        wake_proof_policy="video_only",
        status="draft",
    )
    await repo.save_challenge(challenge)
    dates = starts_at.isoformat() + (f" → {ends_at.isoformat()}" if ends_at else "")
    await send_safe(
        chat_id,
        f"Created draft challenge <code>{code}</code> · {dates}.\n"
        f"In the target group, run <code>/bind_here</code> "
        "(no args — I'll show a button) to bind it. "
        f"Then <code>/admin_start {code}</code> to activate.",
    )


@commands_menu.botspot_command("admin_list_challenges", "List challenges (admin)")
@router.message(Command("admin_list_challenges"))
async def list_challenges(message: Message, repo: Repo) -> None:
    challenges = await repo.list_challenges()
    if not challenges:
        await send_safe(message.chat.id, "No challenges yet.")
        return
    lines = [
        f"<code>{c.code}</code> · {c.status}"
        f" · {c.starts_at.isoformat()}"
        + (f" → {c.ends_at.isoformat()}" if c.ends_at else "")
        + f" · group={c.group_chat_id}"
        for c in challenges
    ]
    await send_safe(message.chat.id, "\n".join(lines))


@commands_menu.botspot_command("admin_start", "Activate a challenge (admin)")
@router.message(Command("admin_start"))
async def start_challenge(message: Message, command: CommandObject, repo: Repo) -> None:
    code = (command.args or "").strip()
    if not code:
        await send_safe(message.chat.id, "Usage: /admin_start &lt;code&gt;")
        return
    c = await repo.get_challenge_by_code(code)
    if not c:
        await send_safe(message.chat.id, f"No challenge <code>{code}</code>.")
        return
    c.status = "active"
    await repo.save_challenge(c)
    await send_safe(message.chat.id, f"Activated <code>{code}</code>.")
    if c.group_chat_id:
        try:
            await send_safe(
                c.group_chat_id,
                f"🌙 Challenge <b>{c.name}</b> is live.\n"
                f"Type <code>/join</code> right here to enroll — "
                "I'll DM you a short setup wizard.",
            )
        except Exception as e:
            logger.warning(
                f"Failed to post announcement to group {c.group_chat_id}: {e}"
            )


@commands_menu.botspot_command("admin_finish", "Finish a challenge (admin)")
@router.message(Command("admin_finish"))
async def finish_challenge(
    message: Message, command: CommandObject, repo: Repo
) -> None:
    code = (command.args or "").strip()
    c = await repo.get_challenge_by_code(code)
    if not c:
        await send_safe(message.chat.id, f"No challenge <code>{code}</code>.")
        return
    c.status = "finished"
    await repo.save_challenge(c)
    await send_safe(message.chat.id, f"Finished <code>{code}</code>.")


async def _unbound_challenges(repo: Repo) -> list[Challenge]:
    all_challenges = await repo.list_challenges()
    return [
        c for c in all_challenges if c.group_chat_id is None and c.status != "finished"
    ]


@commands_menu.botspot_command("bind_here", "Bind this group to a challenge (admin)")
@router.message(Command("bind_here"))
async def bind_here(message: Message, command: CommandObject, repo: Repo) -> None:
    code = (command.args or "").strip()
    if code:
        c = await repo.get_challenge_by_code(code)
        if not c:
            await send_safe(message.chat.id, f"No challenge <code>{code}</code>.")
            return
        c.group_chat_id = message.chat.id
        await repo.save_challenge(c)
        await send_safe(
            message.chat.id,
            f"Bound <code>{code}</code> to this chat (id={message.chat.id}).",
        )
        return

    # No arg → list unbound challenges as buttons.
    challenges = await _unbound_challenges(repo)
    if not challenges:
        await send_safe(
            message.chat.id,
            "No unbound challenges. Create one in DM with /admin_new_challenge.",
        )
        return
    rows = [
        [
            InlineKeyboardButton(
                text=f"{c.code} · {c.status}"
                + (f" · {c.starts_at.isoformat()}" if c.starts_at else ""),
                callback_data=f"bind:{c.code}",
            )
        ]
        for c in challenges
    ]
    kb = InlineKeyboardMarkup(inline_keyboard=rows)
    await send_safe(
        message.chat.id,
        "Pick a challenge to bind to this group:",
        reply_markup=kb,
    )


@router.callback_query(lambda c: c.data and c.data.startswith("bind:"))
async def bind_callback(callback: CallbackQuery, repo: Repo) -> None:
    assert callback.data
    assert callback.message is not None
    code = callback.data.split(":", 1)[1]
    c = await repo.get_challenge_by_code(code)
    if not c:
        await callback.answer(f"No challenge {code}", show_alert=True)
        return
    if c.group_chat_id and c.group_chat_id != callback.message.chat.id:
        await callback.answer(
            f"{code} is already bound elsewhere.", show_alert=True
        )
        return
    c.group_chat_id = callback.message.chat.id
    await repo.save_challenge(c)
    await callback.answer(f"Bound {code} here.")
    try:
        await callback.message.edit_text(
            f"✅ Bound <code>{code}</code> to this chat (id={callback.message.chat.id}).",
            parse_mode="HTML",
        )
    except Exception as e:
        logger.debug(f"edit_text failed: {e}")

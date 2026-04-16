"""Group-chat router — the primary venue of the challenge.

Owns:
- /join in the group: looks up the bound challenge and kicks off a DM wizard.
- Video-note handler: turns кружочки from registered participants into
  bed/wake check-ins with an emoji reaction.
- /bind_here_auto helper: a convenience alias of admin /bind_here (covered in admin.py).
"""

from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    ReactionTypeEmoji,
)
from botspot import commands_menu
from botspot.utils import send_safe
from loguru import logger

from src.db import Repo
from src.group_check_in import already_checked_in, is_on_time, locate_checkin
from src.models import CheckIn
from src.routers.registration import run_setup_wizard
from src.time_utils import challenge_day_for

router = Router(name="group")
router.message.filter(F.chat.type.in_({"group", "supergroup"}))

# Telegram free reaction set — keep these two so no premium is needed.
REACT_ON_TIME = "👍"
REACT_LATE = "🥱"


async def _challenge_for_group(repo: Repo, chat_id: int):
    for c in await repo.list_active_challenges():
        if c.group_chat_id == chat_id:
            return c
    return None


async def _react(bot, chat_id: int, message_id: int, emoji: str) -> None:
    try:
        await bot.set_message_reaction(
            chat_id=chat_id,
            message_id=message_id,
            reaction=[ReactionTypeEmoji(emoji=emoji)],
            is_big=False,
        )
    except TelegramBadRequest as e:
        logger.debug(f"set_message_reaction rejected: {e}")
    except Exception as e:
        logger.warning(f"set_message_reaction failed: {e}")


@commands_menu.botspot_command("join", "Join the group's active challenge")
@router.message(Command("join"))
async def join_from_group(
    message: Message, command: CommandObject, state: FSMContext, repo: Repo
) -> None:
    assert message.from_user
    challenge = await _challenge_for_group(repo, message.chat.id)
    if not challenge:
        await message.reply(
            "No active challenge is bound to this group. "
            "An admin needs to /bind_here &lt;code&gt; first."
        )
        return

    explicit = (command.args or "").strip()
    if explicit and explicit != challenge.code:
        await message.reply(
            f"This group hosts <code>{challenge.code}</code>; ignoring <code>{explicit}</code>."
        )

    # Try to DM the wizard.
    try:
        await send_safe(
            message.from_user.id,
            f"👋 Kicking off setup for <b>{challenge.name}</b> (<code>{challenge.code}</code>).",
        )
    except (TelegramForbiddenError, TelegramBadRequest):
        assert message.bot is not None
        bot_user = await message.bot.me()
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Start chat with the bot",
                        url=f"https://t.me/{bot_user.username}?start=join_{challenge.code}",
                    )
                ]
            ]
        )
        await message.reply(
            f"@{message.from_user.username or message.from_user.full_name} — "
            "press the button, hit Start, then run /join here again.",
            reply_markup=kb,
        )
        return

    user = await run_setup_wizard(message.from_user.id, challenge, state, repo)
    if user is None:
        await message.reply(
            f"@{message.from_user.username or message.from_user.full_name} — "
            "setup was cancelled. Run /join again when you're ready."
        )
        return

    assert challenge.group_chat_id is not None
    await send_safe(
        challenge.group_chat_id,
        f"✅ <b>{message.from_user.full_name}</b> joined. "
        f"Bed {user.bedtime_deadline.strftime('%H:%M')} · "
        f"Wake {user.wakeup_deadline.strftime('%H:%M')}.",
    )


@router.message(F.video_note)
async def video_note_checkin(message: Message, repo: Repo) -> None:
    assert message.from_user
    challenge = await _challenge_for_group(repo, message.chat.id)
    if not challenge:
        return  # not a challenge group — ignore
    assert challenge.id is not None

    user = await repo.get_user(message.from_user.id, challenge.id)
    if not user or not user.active:
        return  # spectators' кружочки are not check-ins

    now_local = datetime.now(ZoneInfo(user.tz))
    field = locate_checkin(now_local)
    if field is None:
        return  # outside any window — ambient кружочек, not a check-in

    day = challenge_day_for(now_local)
    log = await repo.get_log(user.user_id, challenge.id, day)
    if already_checked_in(log, field):
        await _react(message.bot, message.chat.id, message.message_id, REACT_LATE)
        return

    deadline = user.bedtime_deadline if field == "bed" else user.wakeup_deadline
    on_time = is_on_time(now_local, deadline)
    check_in = CheckIn(
        ts=now_local.astimezone(ZoneInfo("UTC")).replace(tzinfo=None),
        kind="video_note",
        on_time=on_time,
    )
    await repo.set_check_in(user.user_id, challenge.id, day, field, check_in)
    await _react(
        message.bot,
        message.chat.id,
        message.message_id,
        REACT_ON_TIME if on_time else REACT_LATE,
    )

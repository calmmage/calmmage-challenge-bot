from datetime import date, datetime

from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from botspot import commands_menu
from botspot.components.features.user_interactions import ask_user, ask_user_choice
from botspot.utils import send_safe
from botspot.utils.admin_filter import AdminFilter
from loguru import logger

from src.db import Repo
from src.models import Challenge, ProofPolicy

router = Router(name="admin")
router.message.filter(AdminFilter())

_POLICIES: list[ProofPolicy] = ["text_or_video", "video_only", "user_choice"]


def _parse_date(s: str) -> date | None:
    try:
        return date.fromisoformat(s.strip())
    except ValueError:
        return None


@commands_menu.botspot_command("admin_new_challenge", "Create a new challenge (admin)")
@router.message(Command("admin_new_challenge"))
async def new_challenge(message: Message, state: FSMContext, repo: Repo) -> None:
    assert message.from_user
    chat_id = message.chat.id

    code = await ask_user(chat_id, "Challenge code (short, unique, e.g. sleep-apr26):", state)
    if not code:
        return
    code = code.strip()
    if await repo.get_challenge_by_code(code):
        await send_safe(chat_id, f"Code <code>{code}</code> already exists.")
        return

    name = await ask_user(chat_id, "Human-readable name:", state) or code

    starts_raw = await ask_user(chat_id, "Start date (YYYY-MM-DD):", state)
    starts_at = _parse_date(starts_raw or "") or date.today()

    ends_raw = await ask_user(chat_id, "End date (YYYY-MM-DD) or 'none':", state)
    ends_at = _parse_date(ends_raw or "") if ends_raw and ends_raw.strip() != "none" else None

    bed_policy = await ask_user_choice(
        chat_id, "Bed proof policy:", {p: p for p in _POLICIES}, state
    )
    wake_policy = await ask_user_choice(
        chat_id, "Wake proof policy:", {p: p for p in _POLICIES}, state
    )

    challenge = Challenge(
        code=code,
        name=name,
        created_by=message.from_user.id,
        created_at=datetime.utcnow(),
        starts_at=starts_at,
        ends_at=ends_at,
        bed_proof_policy=bed_policy or "text_or_video",  # type: ignore[arg-type]
        wake_proof_policy=wake_policy or "text_or_video",  # type: ignore[arg-type]
        status="draft",
    )
    await repo.save_challenge(challenge)
    await send_safe(
        chat_id,
        f"Created draft challenge <code>{code}</code>.\n"
        f"Add the bot to the target group and run <code>/bind_here {code}</code>.\n"
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
        f"<code>{c.code}</code> · {c.status} · bed={c.bed_proof_policy} wake={c.wake_proof_policy}"
        f" · group={c.group_chat_id}"
        for c in challenges
    ]
    await send_safe(message.chat.id, "\n".join(lines))


@commands_menu.botspot_command("admin_start", "Activate a challenge (admin)")
@router.message(Command("admin_start"))
async def start_challenge(
    message: Message, command: CommandObject, repo: Repo
) -> None:
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
                f"DM me <code>/join {c.code}</code> to enroll.",
            )
        except Exception as e:
            logger.warning(f"Failed to post announcement to group {c.group_chat_id}: {e}")


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


@commands_menu.botspot_command("admin_set_policy", "Change a proof policy (admin)")
@router.message(Command("admin_set_policy"))
async def set_policy(
    message: Message, command: CommandObject, repo: Repo
) -> None:
    args = (command.args or "").split()
    if len(args) != 2 or "=" not in args[1]:
        await send_safe(
            message.chat.id,
            "Usage: /admin_set_policy &lt;code&gt; bed=video_only|text_or_video|user_choice\n"
            "or wake=…",
        )
        return
    code, kv = args
    field, value = kv.split("=", 1)
    if field not in ("bed", "wake") or value not in _POLICIES:
        await send_safe(message.chat.id, "Invalid field or value.")
        return
    c = await repo.get_challenge_by_code(code)
    if not c:
        await send_safe(message.chat.id, f"No challenge <code>{code}</code>.")
        return
    if field == "bed":
        c.bed_proof_policy = value  # type: ignore[assignment]
    else:
        c.wake_proof_policy = value  # type: ignore[assignment]
    await repo.save_challenge(c)
    await send_safe(message.chat.id, f"Updated {field} policy to <b>{value}</b>.")


@commands_menu.botspot_command("bind_here", "Bind this group to a challenge (admin)")
@router.message(Command("bind_here"))
async def bind_here(
    message: Message, command: CommandObject, repo: Repo
) -> None:
    code = (command.args or "").strip()
    if not code:
        await send_safe(message.chat.id, "Usage: /bind_here &lt;code&gt;")
        return
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

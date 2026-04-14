from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from botspot import commands_menu
from botspot.components.features.user_interactions import ask_user
from botspot.utils import send_safe
from botspot.utils.admin_filter import AdminFilter
from loguru import logger

from src._app import App
from src.service_account.client import get_service_client, init_service_client

router = Router(name="service_account")


@commands_menu.botspot_command(
    "service_auth", "Authorize the service Telegram account (admin)"
)
@router.message(Command("service_auth"), AdminFilter())
async def service_auth(message: Message, state: FSMContext, app: App) -> None:
    chat_id = message.chat.id
    if not app.config.sleep_bot_service_api_id or not app.config.sleep_bot_service_api_hash:
        await send_safe(
            chat_id,
            "Service account api_id/api_hash not configured in env. Set "
            "<code>SLEEP_BOT_SERVICE_API_ID</code> and <code>SLEEP_BOT_SERVICE_API_HASH</code>.",
        )
        return
    if not app.config.sleep_bot_service_phone:
        await send_safe(chat_id, "Set <code>SLEEP_BOT_SERVICE_PHONE</code> in env first.")
        return

    client = get_service_client() or init_service_client(app)
    if await client.connect_if_authorized():
        await send_safe(chat_id, "Service account already authorized. Nothing to do.")
        return

    phone = app.config.sleep_bot_service_phone
    try:
        phone_code_hash = await client.send_code(phone)
    except Exception as e:
        await send_safe(chat_id, f"send_code failed: {e}")
        return

    code_raw = await ask_user(
        chat_id,
        "Telegram sent a login code to the service account's phone. "
        "Paste it here as <code>1 2 3 4 5</code> (spaces between digits).",
        state,
        timeout=300.0,
    )
    if not code_raw:
        await send_safe(chat_id, "No code received. Aborting.")
        return
    if " " not in code_raw.strip():
        await send_safe(chat_id, "Please insert spaces between digits and try again.")
        return
    code = code_raw.replace(" ", "")

    password = None
    try:
        await client.sign_in(phone, code, phone_code_hash)
    except Exception as e:
        if "password" not in str(e).lower():
            await send_safe(chat_id, f"Sign-in failed: {e}")
            return
        password = await ask_user(
            chat_id, "Two-factor password:", state, timeout=300.0, cleanup=True
        )
        if not password:
            await send_safe(chat_id, "No password. Aborting.")
            return
        try:
            await client.sign_in(phone, code, phone_code_hash, password=password)
        except Exception as e2:
            await send_safe(chat_id, f"Sign-in with password failed: {e2}")
            return

    if await client.connect_if_authorized():
        await send_safe(chat_id, "✅ Service account authorized.")
    else:
        logger.error("Service account not authorized after sign-in")
        await send_safe(chat_id, "Something went wrong; check logs.")

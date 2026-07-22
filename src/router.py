from aiogram import Router, html
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from botspot import commands_menu
from botspot.i18n import t
from botspot.utils import is_admin, send_safe

from src._app import App

router = Router(name="main")


@commands_menu.botspot_command("start", "Start the bot")
@router.message(CommandStart(), lambda m: m.chat.type == "private")
async def start_handler(message: Message, app: App):
    assert message.from_user is not None
    name = html.bold(message.from_user.full_name)
    key = "start_admin" if is_admin(message.from_user) else "start_user"
    await send_safe(message.chat.id, t(key, name=name))


@commands_menu.botspot_command("help", "Show help")
@router.message(Command("help"), lambda m: m.chat.type == "private")
async def help_handler(message: Message, app: App):
    await send_safe(message.chat.id, t("help", name=app.name))

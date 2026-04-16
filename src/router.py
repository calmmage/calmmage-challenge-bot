from aiogram import Router, html
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from botspot import commands_menu
from botspot.utils import is_admin, send_safe

from src._app import App

router = Router(name="main")


@commands_menu.botspot_command("start", "Start the bot")
@router.message(CommandStart(), lambda m: m.chat.type == "private")
async def start_handler(message: Message, app: App):
    assert message.from_user is not None
    name = html.bold(message.from_user.full_name)
    if is_admin(message.from_user):
        text = (
            f"Hi {name} 👋 — you're an <b>admin</b>.\n\n"
            "<b>Quickstart:</b>\n"
            "• /admin_new_challenge — create a challenge (here in DM)\n"
            "• in the group: /bind_here — bind the challenge\n"
            "• /admin_start &lt;code&gt; — go live\n\n"
            "<b>More:</b> /admin_list_challenges · /admin_finish · /help"
        )
    else:
        text = (
            f"Hi {name}!\n\n"
            "<b>How to join:</b>\n"
            "• /join — pick your challenge (buttons)\n"
            "• follow the short setup wizard\n\n"
            "<b>How to participate:</b>\n"
            "• post 🎥 video notes (кружочки) in the challenge group\n"
            "• one at bedtime, one at wake-up → that's your check-in\n"
            "• 👍 on time / 🥱 late\n\n"
            "Type /help for more."
        )
    await send_safe(message.chat.id, text)


@commands_menu.botspot_command("help", "Show help")
@router.message(Command("help"), lambda m: m.chat.type == "private")
async def help_handler(message: Message, app: App):
    await send_safe(
        message.chat.id,
        f"<b>{app.name}</b>\n\n"
        "<b>In the challenge group:</b>\n"
        "/join — enroll (I'll DM you the setup wizard)\n"
        "🎥 post a video note at bed and at wake — that's your check-in\n\n"
        "<b>In DM (settings &amp; private history):</b>\n"
        "/status — today's log, streak, deadlines\n"
        "/history — last 14 days\n"
        "/tighten_bed HH:MM — move bedtime earlier (never later)\n"
        "/tighten_wake HH:MM — move wake-up earlier\n"
        "/how_to_share_online — bonus 'last seen' setup\n\n"
        "<b>Admin (DM):</b>\n"
        "/admin_new_challenge — create a challenge\n"
        "/admin_list_challenges\n"
        "/admin_start &lt;code&gt; — activate a challenge\n"
        "/admin_finish &lt;code&gt;\n"
        "/bind_here &lt;code&gt; — bind the current group to a challenge (run in group)\n"
        "/setup_telethon — authorize the Telethon service account (bonus)",
    )

from aiogram import Router, html
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from botspot import commands_menu
from botspot.utils import send_safe

from src._app import App

router = Router(name="main")


@commands_menu.botspot_command("start", "Start the bot")
@router.message(CommandStart(), lambda m: m.chat.type == "private")
async def start_handler(message: Message, app: App):
    assert message.from_user is not None
    await send_safe(
        message.chat.id,
        f"Hello, {html.bold(message.from_user.full_name)}!\n"
        f"Welcome to {app.name}.\n"
        "Use /join &lt;challenge_code&gt; to enter an active challenge, "
        "or /help to see what's available.",
    )


@commands_menu.botspot_command("help", "Show help")
@router.message(Command("help"), lambda m: m.chat.type == "private")
async def help_handler(message: Message, app: App):
    await send_safe(
        message.chat.id,
        f"<b>{app.name}</b>\n\n"
        "<b>Participants:</b>\n"
        "/join &lt;code&gt; — join an active challenge\n"
        "/status — today's log, streak, deadlines\n"
        "/history — last 14 days\n"
        "/tighten_bed HH:MM — move bedtime earlier (never later)\n"
        "/tighten_wake HH:MM — move wake-up earlier\n"
        "/how_to_share_online — instructions for the bonus online-status feature\n\n"
        "<b>Admin:</b>\n"
        "/admin_new_challenge — create a challenge\n"
        "/admin_list_challenges\n"
        "/admin_start &lt;code&gt; — activate a challenge\n"
        "/admin_finish &lt;code&gt;\n"
        "/admin_set_policy &lt;code&gt; wake=video_only|text_or_video|user_choice\n"
        "/bind_here &lt;code&gt; — bind this group chat to a challenge\n"
        "/service_auth — authorize the service Telegram account",
    )

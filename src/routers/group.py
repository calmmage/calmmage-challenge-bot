from aiogram import F, Router
from aiogram.types import Message
from botspot.utils import send_safe

router = Router(name="group")
router.message.filter(F.chat.type.in_({"group", "supergroup"}))


async def _bot_mentioned(message: Message) -> bool:
    if not message.text and not message.caption:
        return False
    text = message.text or message.caption or ""
    me = (await message.bot.me()).username if message.bot else None
    if me and f"@{me}".lower() in text.lower():
        return True
    if message.reply_to_message and message.reply_to_message.from_user:
        return bool(message.reply_to_message.from_user.is_bot)
    return False


@router.message()
async def group_gatekeeper(message: Message) -> None:
    if not await _bot_mentioned(message):
        return
    me = (await message.bot.me()).username if message.bot else None
    link = f"https://t.me/{me}" if me else "(DM me)"
    await send_safe(
        message.chat.id,
        f"➡️ Let's talk in DM: {link}",
        reply_to_message_id=message.message_id,
    )

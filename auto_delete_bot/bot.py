import asyncio
import logging
from aiogram import Bot, Dispatcher, executor, types
from telethon import TelegramClient, events
from telethon.sessions import StringSession

from .config import BOT_TOKEN, API_ID, API_HASH, SESSION_STRING

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AutoDeleteBot")

# Aiogram bot setup
bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)

# Telethon client setup
user_client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

# Deletion timer storage
delete_times = {}

@dp.message_handler(commands=["start"], chat_type=[types.ChatType.PRIVATE])
async def start_cmd(message: types.Message):
    logger.info(f"User started the bot: {message.from_user.id} - @{message.from_user.username}")
    await message.reply("Welcome to Auto Delete Bot!\nUse /set_time <seconds> in your group.")

@dp.message_handler(commands=["set_time"], chat_type=[types.ChatType.GROUP, types.ChatType.SUPERGROUP])
async def set_time_cmd(message: types.Message):
    try:
        seconds = int(message.get_args())
        chat_id = message.chat.id
        delete_times[chat_id] = seconds
        await message.reply(f"Messages will be deleted after {seconds} seconds.")
        logger.info(f"Set delete time in {chat_id} to {seconds} seconds.")

        # Make the user (Telethon session) join the group
        try:
            await user_client.join_chat(chat_id)
            logger.info(f"User client joined chat {chat_id}")
        except Exception as e:
            logger.warning(f"User client failed to join chat {chat_id}: {e}")
            await message.reply(f"User could not join the group: {e}")
            return

        # Promote the user client as admin
        try:
            user_me = await user_client.get_me()
            await bot.promote_chat_member(
                chat_id=chat_id,
                user_id=user_me.id,
                can_manage_chat=True,
                can_change_info=True,
                can_delete_messages=True,
                can_invite_users=True,
                can_restrict_members=True,
                can_pin_messages=True,
                can_promote_members=True,
                can_manage_video_chats=True
            )
            logger.info(f"Promoted user client as admin in chat {chat_id}")
            await message.reply("User has joined and has been promoted to admin.")
        except Exception as e:
            logger.warning(f"Failed to promote user: {e}")
            await message.reply(f"User joined, but promotion failed: {e}")

    except:
        await message.reply("Usage: /set_time <seconds>")

@dp.message_handler(commands=["get_time"], chat_type=[types.ChatType.GROUP, types.ChatType.SUPERGROUP])
async def get_time_cmd(message: types.Message):
    seconds = delete_times.get(message.chat.id)
    if seconds:
        await message.reply(f"Messages will be deleted after {seconds} seconds.")
    else:
        await message.reply("No delete time set. Use /set_time <seconds>.")

@dp.message_handler(commands=["remove"], chat_type=[types.ChatType.GROUP, types.ChatType.SUPERGROUP])
async def remove_cmd(message: types.Message):
    delete_times.pop(message.chat.id, None)
    await message.reply("Auto delete disabled for this group.")
    logger.info(f"Deleted timer for chat {message.chat.id}")

@dp.message_handler(content_types=types.ContentType.ANY, chat_type=[types.ChatType.GROUP, types.ChatType.SUPERGROUP])
async def bot_delete_handler(message: types.Message):
    chat_id = message.chat.id
    delete_after = delete_times.get(chat_id)
    if delete_after:
        await asyncio.sleep(delete_after)
        try:
            await bot.delete_message(chat_id, message.message_id)
            logger.info(f"Bot deleted message {message.message_id} in chat {chat_id}")
        except Exception as e:
            logger.warning(f"Bot couldn't delete message {message.message_id}: {e}")

@user_client.on(events.NewMessage(chats=lambda e: e.is_group or e.is_channel))
async def user_delete_handler(event):
    chat_id = event.chat_id
    delete_after = delete_times.get(chat_id)
    if delete_after:
        await asyncio.sleep(delete_after)
        try:
            await event.delete()
            logger.info(f"User deleted message {event.id} in chat {chat_id}")
        except Exception as e:
            logger.warning(f"User couldn't delete message {event.id}: {e}")

async def main():
    await user_client.start()
    logger.info("User client started")
    await dp.start_polling()

def run():
    asyncio.run(main())

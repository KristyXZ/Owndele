import asyncio
import logging
from aiohttp import web
from pyrogram import Client, filters
from pyrogram.types import Message, ChatPrivileges
from bot.config import BOT_TOKEN, API_ID, API_HASH, SESSION_STRING

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AutoDeleteBot")

bot = Client("bot", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)
user_client = Client("user", session_string=SESSION_STRING, api_id=API_ID, api_hash=API_HASH)

delete_times = {}

@bot.on_message(filters.command("start") & filters.private)
async def start_handler(client, message):
    logger.info("Start command triggered.")
    await message.reply("✅ Hello! Bot is working.")

@bot.on_message(filters.command("set_time") & filters.group)
async def set_time_cmd(_, message: Message):
    try:
        seconds = int(message.text.split(maxsplit=1)[1])
        chat_id = message.chat.id
        delete_times[chat_id] = seconds
        await message.reply(f"Messages will be deleted after {seconds} seconds.")

        try:
            await user_client.join_chat(chat_id)
            logger.info(f"User joined chat {chat_id}")
        except Exception as e:
            logger.warning(f"User failed to join: {e}")
            await message.reply(f"User could not join group: {e}")
            return

        try:
            user = await user_client.get_me()
            await bot.promote_chat_member(
                chat_id=chat_id,
                user_id=user.id,
                privileges=ChatPrivileges(
                    can_manage_chat=True,
                    can_delete_messages=True,
                    can_restrict_members=True,
                    can_promote_members=True,
                    can_change_info=True,
                    can_invite_users=True,
                    can_pin_messages=True,
                    can_manage_video_chats=True
                )
            )
            await message.reply("✅ User joined and promoted to admin.")
        except Exception as e:
            logger.warning(f"Promotion failed: {e}")
            await message.reply(f"User joined, but promotion failed: {e}")

    except:
        await message.reply("⚠️ Usage: /set_time <seconds>")

@bot.on_message(filters.command("get_time") & filters.group)
async def get_time_cmd(_, message: Message):
    seconds = delete_times.get(message.chat.id)
    if seconds:
        await message.reply(f"⏲ Messages will be deleted after {seconds} seconds.")
    else:
        await message.reply("❌ No delete time set. Use /set_time <seconds>.")

@bot.on_message(filters.command("remove") & filters.group)
async def remove_cmd(_, message: Message):
    delete_times.pop(message.chat.id, None)
    await message.reply("🗑 Auto delete disabled for this group.")

@bot.on_message(filters.group)
async def bot_delete_handler(_, message: Message):
    chat_id = message.chat.id
    delete_after = delete_times.get(chat_id)
    if delete_after:
        await asyncio.sleep(delete_after)
        try:
            await bot.delete_messages(chat_id, message.id)
        except Exception as e:
            logger.warning(f"Bot failed to delete message {message.id}: {e}")

@user_client.on_message(filters.group)
async def user_delete_handler(_, message: Message):
    chat_id = message.chat.id
    delete_after = delete_times.get(chat_id)
    if delete_after:
        await asyncio.sleep(delete_after)
        try:
            await user_client.delete_messages(chat_id, message.id)
        except Exception as e:
            logger.warning(f"User failed to delete message {message.id}: {e}")

# Health check server for Koyeb
async def healthcheck(request):
    return web.Response(text="OK")

async def start_webserver():
    app = web.Application()
    app.router.add_get("/", healthcheck)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()

async def start_bot():
    await bot.start()
    await user_client.start()
    logger.info("Both clients started.")

    await start_webserver()  # Start HTTP server for health check

    await asyncio.Event().wait()  # Keep running

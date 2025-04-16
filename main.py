import asyncio
import logging
from aiohttp import web
from bot.core import start_bot

logging.basicConfig(level=logging.INFO)

async def handle(request):
    return web.Response(text="Bot is alive!")

async def start_web():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, port=8080)
    await site.start()
    logging.info("✅ Web server started on port 8080")

async def main():
    await asyncio.gather(
        start_bot(),
        start_web()
    )

if __name__ == "__main__":
    asyncio.run(main())

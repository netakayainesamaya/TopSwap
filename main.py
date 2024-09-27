import subprocess
import asyncio
from contextlib import suppress
from aiohttp import web
import requests
import os

from bot.utils.launcher import process
from bot.config.config import settings  # пример импорта settings

# Установка Chromium (вместо Google Chrome)
subprocess.run(["bash", "chrome_install.sh"])

print(f"API_ID: {settings.API_ID}, API_HASH: {settings.API_HASH}")

# Имитация простого веб-сервера для Render
async def handle(request):
    return web.Response(text="Bot is running")

async def start_server():
    app = web.Application()
    app.add_routes([web.get('/', handle)])
    runner = web.AppRunner(app)
    await runner.setup()
    port = os.getenv("PORT", 8000)  # Получаем порт от Render или используем 8000 по умолчанию
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"Serving on port {port}")

async def main():
    await asyncio.gather(
        process(),       # Основная логика бота
        start_server()   # Запуск веб-сервера для Render
    )

if __name__ == '__main__':
    with suppress(KeyboardInterrupt):
        asyncio.run(main())

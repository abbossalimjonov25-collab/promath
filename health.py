"""
Render.com Worker turida bot polling rejimida ishlaydi.
Cron-job.org botni uyg'otib turish uchun health check endpoint kerak bo'lsa,
quyidagi kichik HTTP server ishga tushirish mumkin.

Lekin Worker (polling) rejimida bu shart emas.
Agar Web Service sifatida deploy qilsangiz, ushbu faylni ishlatishingiz mumkin.
"""

from aiohttp import web
import asyncio
import logging

logger = logging.getLogger(__name__)


async def health_check(request):
    return web.Response(text="OK", status=200)


async def start_health_server():
    app = web.Application()
    app.router.add_get("/", health_check)
    app.router.add_get("/health", health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()
    logger.info("Health check server: http://0.0.0.0:8080/health")

import os
import asyncio
import logging
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ConversationHandler, filters
)
from db import init_db
from user import (
    start, check_sub_callback, menu_callback, enter_test_command,
    receive_test_code, receive_user_answers, cancel as user_cancel,
    WAIT_TEST_CODE, WAIT_USER_ANSWERS
)
from admin import (
    admin_panel, admin_callback, receive_answers, receive_subject,
    cancel as admin_cancel, WAIT_ANSWERS, WAIT_SUBJECT
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def build_app():
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    app = Application.builder().token(BOT_TOKEN).build()

    test_conv = ConversationHandler(
        entry_points=[
            CommandHandler("test", enter_test_command),
            CallbackQueryHandler(menu_callback, pattern="^enter_test$"),
        ],
        states={
            WAIT_TEST_CODE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_test_code)
            ],
            WAIT_USER_ANSWERS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_user_answers)
            ],
        },
        fallbacks=[CommandHandler("cancel", user_cancel)],
        allow_reentry=True,
        per_message=False,
    )

    admin_create_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(admin_callback, pattern="^admin_create_test$"),
        ],
        states={
            WAIT_ANSWERS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_answers)
            ],
            WAIT_SUBJECT: [
                CallbackQueryHandler(receive_subject, pattern="^subj_")
            ],
        },
        fallbacks=[CommandHandler("cancel", admin_cancel)],
        allow_reentry=True,
        per_message=False,
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(test_conv)
    app.add_handler(admin_create_conv)
    app.add_handler(CallbackQueryHandler(check_sub_callback, pattern="^check_sub$"))
    app.add_handler(CallbackQueryHandler(admin_callback, pattern="^admin_"))
    app.add_handler(CallbackQueryHandler(admin_callback, pattern="^end_"))
    app.add_handler(CallbackQueryHandler(menu_callback, pattern="^(about|go_admin)$"))

    return app

async def main():
    await init_db()
    logger.info("✅ Database tayyor!")

    BOT_TOKEN = os.getenv("BOT_TOKEN")
    RENDER_URL = os.getenv("RENDER_EXTERNAL_URL", "")
    PORT = int(os.getenv("PORT", 10000))

    app = build_app()

    if RENDER_URL:
        logger.info(f"Webhook mode: {RENDER_URL}")
        await app.bot.set_webhook(
            url=f"{RENDER_URL}/{BOT_TOKEN}",
            allowed_updates=["message", "callback_query"]
        )
        async with app:
            await app.start()
            await app.updater.start_webhook(
                listen="0.0.0.0",
                port=PORT,
                url_path=BOT_TOKEN,
            )
            logger.info(f"Bot ishga tushdi! Port: {PORT}")
            await asyncio.Event().wait()
    else:
        logger.info("Polling mode (lokal)")
        async with app:
            await app.start()
            await app.updater.start_polling(drop_pending_updates=True)
            logger.info("Polling boshlandi!")
            await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())

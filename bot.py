import asyncio
import logging
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ConversationHandler, filters
)
from config import BOT_TOKEN, ADMIN_ID
from database.db import init_db
from handlers.user import (
    start, check_sub_callback, menu_callback, enter_test_command,
    receive_test_code, receive_user_answers, cancel as user_cancel,
    WAIT_TEST_CODE, WAIT_USER_ANSWERS
)
from handlers.admin import (
    admin_panel, admin_callback, receive_answers, receive_subject,
    cancel as admin_cancel, WAIT_ANSWERS, WAIT_SUBJECT
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def post_init(application):
    await init_db()
    logger.info("Bot ishga tushdi!")

def main():
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    # Test conversation (O'quvchi)
    test_conv = ConversationHandler(
        entry_points=[
            CommandHandler("test", enter_test_command),
            CallbackQueryHandler(menu_callback, pattern="^enter_test$"),
        ],
        states={
            WAIT_TEST_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_test_code)],
            WAIT_USER_ANSWERS: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_user_answers)],
        },
        fallbacks=[CommandHandler("cancel", user_cancel)],
        allow_reentry=True
    )

    # Admin test yaratish conversation
    admin_create_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_callback, pattern="^admin_create_test$")],
        states={
            WAIT_ANSWERS: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_answers)],
            WAIT_SUBJECT: [CallbackQueryHandler(receive_subject, pattern="^subj_")],
        },
        fallbacks=[CommandHandler("cancel", admin_cancel)],
        allow_reentry=True
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(test_conv)
    app.add_handler(admin_create_conv)
    app.add_handler(CallbackQueryHandler(check_sub_callback, pattern="^check_sub$"))
    app.add_handler(CallbackQueryHandler(admin_callback, pattern="^admin_"))
    app.add_handler(CallbackQueryHandler(admin_callback, pattern="^end_"))
    app.add_handler(CallbackQueryHandler(menu_callback, pattern="^(about|admin_main)$"))

    logger.info("Bot polling boshlandi...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()

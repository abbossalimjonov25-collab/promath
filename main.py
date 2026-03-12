import os
import asyncio
import logging
import threading
import json
import os as _os
from flask import Flask, request, jsonify, send_from_directory
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, MenuButtonWebApp, ChatMember
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ConversationHandler, filters
)
from db import (init_db, register_user, get_test, get_all_active_tests, get_test_any,
                submit_answers, end_test, get_test_results, check_already_submitted,
                create_test, get_all_tests, get_submission, get_user, update_user_name)
from test_checker import generate_test_code, parse_answers, check_answers, answers_dict_to_string, parse_answers_to_dict
from pdf_generator import generate_results_pdf, generate_certificate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
CHANNEL_ID = os.getenv("CHANNEL_ID")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "")
RENDER_URL = os.getenv("RENDER_EXTERNAL_URL", "")

app = Flask(__name__, static_folder=_os.path.join(_os.path.dirname(__file__), "static"))
ptb_app = None
loop = None

WAIT_NAME = 1

# ========== FLASK API ROUTES ==========

@app.route("/")
def index():
    return send_from_directory(_os.path.join(_os.path.dirname(__file__), "static"), "test.html")

@app.route("/admin-app")
def admin_app():
    return send_from_directory(_os.path.join(_os.path.dirname(__file__), "static"), "admin.html")

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    if ptb_app and loop:
        data = request.get_json(force=True)
        update = Update.de_json(data, ptb_app.bot)
        asyncio.run_coroutine_threadsafe(ptb_app.process_update(update), loop)
    return "ok"

@app.route("/api/test/<test_code>")
def api_get_test(test_code):
    async def _get():
        return await get_test(test_code.upper())
    future = asyncio.run_coroutine_threadsafe(_get(), loop)
    test = future.result(timeout=10)
    if not test:
        return jsonify({"error": "Test topilmadi yoki yakunlangan"}), 404
    return jsonify({
        "test_code": test['test_code'],
        "subject": test['subject'],
        "total_questions": test['total_questions'],
        "questions": [{"number": i, "options": ["A", "B", "C", "D"]} for i in range(1, test['total_questions'] + 1)]
    })

@app.route("/api/submit", methods=["POST"])
def api_submit():
    data = request.get_json()
    test_code = data.get("test_code", "").upper()
    user_id = int(data.get("user_id", 0))
    user_answers = data.get("answers", {})
    user_name = data.get("user_name", "O'quvchi")

    async def _submit():
        test = await get_test(test_code)
        if not test:
            return {"error": "Test topilmadi"}, 404
        already = await check_already_submitted(test_code, user_id)
        if already:
            sub = await get_submission(test_code, user_id)
            return {"already_submitted": True, "score": sub['score'], "total": sub['total'], "percentage": sub['percentage']}, 200
        correct_answers = parse_answers(test['answers'])
        score, total, percentage, detailed = check_answers(correct_answers, user_answers)
        await register_user(user_id, user_name, None)
        await submit_answers(test_code, user_id, json.dumps(user_answers), score, total, percentage)
        return {"score": score, "total": total, "percentage": round(percentage, 1), "detailed": {str(k): v for k, v in detailed.items()}}, 200

    future = asyncio.run_coroutine_threadsafe(_submit(), loop)
    result, status = future.result(timeout=15)
    return jsonify(result), status

@app.route("/api/user/<int:user_id>")
def api_get_user(user_id):
    async def _get():
        return await get_user(user_id)
    future = asyncio.run_coroutine_threadsafe(_get(), loop)
    user = future.result(timeout=10)
    if not user:
        return jsonify({"error": "Topilmadi"}), 404
    return jsonify({"user_id": user['user_id'], "full_name": user['full_name'], "username": user['username']})

@app.route("/api/user/update-name", methods=["POST"])
def api_update_name():
    data = request.get_json()
    user_id = int(data.get("user_id", 0))
    new_name = data.get("full_name", "").strip()
    if not new_name or len(new_name) < 2:
        return jsonify({"error": "Ism juda qisqa"}), 400
    if len(new_name) > 50:
        return jsonify({"error": "Ism juda uzun"}), 400
    async def _update():
        await update_user_name(user_id, new_name)
    asyncio.run_coroutine_threadsafe(_update(), loop).result(timeout=10)
    return jsonify({"success": True, "full_name": new_name})

@app.route("/api/admin/create-test", methods=["POST"])
def api_create_test():
    data = request.get_json()
    admin_id = int(data.get("admin_id", 0))
    if admin_id != ADMIN_ID:
        return jsonify({"error": "Ruxsat yo'q"}), 403
    answers_input = data.get("answers", "")
    subject = data.get("subject", "Matematika")
    parsed = parse_answers(answers_input)
    if not parsed:
        letters = answers_input.upper().replace(" ", "")
        if all(c.isalpha() for c in letters) and len(letters) > 0:
            parsed = {i+1: l for i, l in enumerate(letters)}
        else:
            return jsonify({"error": "Kalitlar formati noto'g'ri"}), 400
    test_code = generate_test_code()
    answers_str = answers_dict_to_string(parsed)
    async def _create():
        await create_test(test_code, answers_str, len(parsed), admin_id, subject)
    asyncio.run_coroutine_threadsafe(_create(), loop).result(timeout=10)
    return jsonify({"test_code": test_code, "total_questions": len(parsed), "subject": subject})

@app.route("/api/admin/tests/<int:admin_id>")
def api_get_tests(admin_id):
    if admin_id != ADMIN_ID:
        return jsonify({"error": "Ruxsat yo'q"}), 403
    async def _get():
        return await get_all_tests(admin_id)
    future = asyncio.run_coroutine_threadsafe(_get(), loop)
    tests = future.result(timeout=10)
    return jsonify([{
        "test_code": t['test_code'], "subject": t['subject'],
        "total_questions": t['total_questions'], "is_active": t['is_active'],
        "created_at": t['created_at'].strftime('%d.%m.%Y %H:%M')
    } for t in tests])

@app.route("/api/admin/end-test", methods=["POST"])
def api_end_test():
    data = request.get_json()
    admin_id = int(data.get("admin_id", 0))
    test_code = data.get("test_code", "").upper()
    if admin_id != ADMIN_ID:
        return jsonify({"error": "Ruxsat yo'q"}), 403
    async def _end():
        test = await get_test_any(test_code)
        if not test:
            return None, None
        await end_test(test_code)
        results = await get_test_results(test_code)
        return test, results
    future = asyncio.run_coroutine_threadsafe(_end(), loop)
    test, results = future.result(timeout=10)
    if test is None:
        return jsonify({"error": "Test topilmadi"}), 404
    if results:
        async def _send_certs():
            for rank, row in enumerate(results, 1):
                try:
                    cert_buffer = generate_certificate(
                        user_name=row['full_name'] or "O'quvchi",
                        subject=test['subject'], score=row['score'],
                        total=row['total'], percentage=row['percentage'],
                        test_code=test_code, rank=rank)
                    await ptb_app.bot.send_document(
                        chat_id=row['user_id'], document=cert_buffer,
                        filename=f"sertifikat_{test_code}.pdf",
                        caption=f"🎓 *Tabriklaymiz!*\n\n📚 {test['subject']}\n✅ {row['score']}/{row['total']} ({row['percentage']:.1f}%)\n🏆 {rank}-o'rin",
                        parse_mode="Markdown")
                except Exception as e:
                    logger.error(f"Sertifikat xato {row['user_id']}: {e}")
        asyncio.run_coroutine_threadsafe(_send_certs(), loop)
    return jsonify({"success": True, "participants": len(results) if results else 0})

@app.route("/api/admin/results/<test_code>")
def api_get_results(test_code):
    async def _get():
        return await get_test_results(test_code.upper())
    future = asyncio.run_coroutine_threadsafe(_get(), loop)
    results = future.result(timeout=10)
    return jsonify([{
        "rank": i+1, "full_name": r['full_name'] or "Noma'lum",
        "username": r['username'], "score": r['score'],
        "total": r['total'], "percentage": round(r['percentage'], 1)
    } for i, r in enumerate(results)])

# ========== HELPERS ==========

def get_main_keyboard(user_id):
    miniapp_url = f"{RENDER_URL}/"
    keyboard = [
        [InlineKeyboardButton("📝 Testga kirish", web_app=WebAppInfo(url=miniapp_url))],
        [InlineKeyboardButton("👤 Profilim", callback_data="profile")],
        [InlineKeyboardButton("ℹ️ Bot haqida", callback_data="about")],
    ]
    if user_id == ADMIN_ID:
        admin_url = f"{RENDER_URL}/admin-app"
        keyboard.insert(0, [InlineKeyboardButton("👨‍💼 Admin panel", web_app=WebAppInfo(url=admin_url))])
    return InlineKeyboardMarkup(keyboard)

async def check_subscription(bot, user_id):
    if not CHANNEL_ID:
        return True
    try:
        channel = CHANNEL_ID.strip()
        if channel.lstrip('-').isdigit():
            channel = int(channel)
        member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
        return member.status in [ChatMember.MEMBER, ChatMember.ADMINISTRATOR, ChatMember.OWNER]
    except Exception as e:
        logger.warning(f"Obuna tekshirishda xato: {e}")
        return True

# ========== BOT HANDLERS ==========

async def start(update: Update, context):
    user = update.effective_user
    await register_user(user.id, user.full_name, user.username)
    is_sub = await check_subscription(context.bot, user.id)

    if not is_sub:
        ch_link = f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}" if CHANNEL_USERNAME else "https://t.me"
        keyboard = [
            [InlineKeyboardButton("📢 Kanalga obuna bo'lish", url=ch_link)],
            [InlineKeyboardButton("✅ Obunani tekshirish", callback_data="check_sub")]
        ]
        await update.message.reply_text(
            f"👋 Salom, *{user.first_name}*!\n\n"
            f"⚠️ Botdan foydalanish uchun avval kanalimizga obuna bo'ling!\n\n"
            f"Obuna bo'lgandan so'ng *✅ Obunani tekshirish* tugmasini bosing.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return

    await update.message.reply_text(
        f"🎉 Xush kelibsiz, *{user.first_name}*!\n\n"
        f"🎓 *Milliy Sertifikat Test Boti*\n\n"
        f"Testga kirish uchun quyidagi tugmani bosing:",
        reply_markup=get_main_keyboard(user.id),
        parse_mode="Markdown"
    )

async def check_sub_callback(update: Update, context):
    query = update.callback_query
    await query.answer(cache_time=0)
    user = query.from_user
    is_sub = await check_subscription(context.bot, user.id)

    if not is_sub:
        ch_link = f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}" if CHANNEL_USERNAME else "https://t.me"
        keyboard = [
            [InlineKeyboardButton("📢 Kanalga obuna bo'lish", url=ch_link)],
            [InlineKeyboardButton("✅ Obunani tekshirish", callback_data="check_sub")]
        ]
        await query.answer("❌ Siz hali obuna bo'lmadingiz!", show_alert=True)
        await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))
        return

    await register_user(user.id, user.full_name, user.username)
    await query.edit_message_text(
        f"✅ *Obuna tasdiqlandi!*\n\n"
        f"🎉 Xush kelibsiz, *{user.first_name}*!\n\n"
        f"🎓 *Milliy Sertifikat Test Boti*\n\n"
        f"Testga kirish uchun quyidagi tugmani bosing:",
        reply_markup=get_main_keyboard(user.id),
        parse_mode="Markdown"
    )

async def profile_callback(update: Update, context):
    query = update.callback_query
    await query.answer()
    user = query.from_user

    async def _get():
        return await get_user(user.id)
    future = asyncio.run_coroutine_threadsafe(_get(), loop)
    db_user = future.result(timeout=10)

    name = db_user['full_name'] if db_user else user.full_name
    username = f"@{user.username}" if user.username else "Yo'q"

    keyboard = [
        [InlineKeyboardButton("✏️ Ismni o'zgartirish", callback_data="edit_name")],
        [InlineKeyboardButton("🔙 Orqaga", callback_data="back_menu")],
    ]
    await query.edit_message_text(
        f"👤 *Profilingiz*\n\n"
        f"📛 Ism: *{name}*\n"
        f"🆔 ID: `{user.id}`\n"
        f"👤 Username: {username}\n\n"
        f"Ismingizni o'zgartirish uchun tugmani bosing:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def edit_name_callback(update: Update, context):
    query = update.callback_query
    await query.answer()
    context.user_data['editing_name'] = True
    context.user_data['edit_message_id'] = query.message.message_id

    keyboard = [[InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_edit")]]
    await query.edit_message_text(
        "✏️ *Yangi ismingizni yozing:*\n\n"
        "Misol: `Abdullayev Jasur`\n\n"
        "_(2-50 ta belgi, faqat matn)_",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return WAIT_NAME

async def receive_new_name(update: Update, context):
    if not context.user_data.get('editing_name'):
        return
    user = update.effective_user
    new_name = update.message.text.strip()

    await update.message.delete()

    if len(new_name) < 2:
        await context.bot.send_message(
            chat_id=user.id,
            text="❌ Ism juda qisqa! Kamida 2 ta harf kiriting."
        )
        return WAIT_NAME

    if len(new_name) > 50:
        await context.bot.send_message(
            chat_id=user.id,
            text="❌ Ism juda uzun! 50 ta belgidan oshmasin."
        )
        return WAIT_NAME

    async def _update():
        await update_user_name(user.id, new_name)
    asyncio.run_coroutine_threadsafe(_update(), loop).result(timeout=10)

    context.user_data['editing_name'] = False

    keyboard = [
        [InlineKeyboardButton("✏️ Yana o'zgartirish", callback_data="edit_name")],
        [InlineKeyboardButton("🔙 Menyu", callback_data="back_menu")],
    ]
    await context.bot.send_message(
        chat_id=user.id,
        text=f"✅ *Ism muvaffaqiyatli o'zgartirildi!*\n\n📛 Yangi ism: *{new_name}*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return ConversationHandler.END

async def cancel_edit_callback(update: Update, context):
    query = update.callback_query
    await query.answer()
    context.user_data['editing_name'] = False
    user = query.from_user

    async def _get():
        return await get_user(user.id)
    future = asyncio.run_coroutine_threadsafe(_get(), loop)
    db_user = future.result(timeout=10)
    name = db_user['full_name'] if db_user else user.full_name
    username = f"@{user.username}" if user.username else "Yo'q"

    keyboard = [
        [InlineKeyboardButton("✏️ Ismni o'zgartirish", callback_data="edit_name")],
        [InlineKeyboardButton("🔙 Orqaga", callback_data="back_menu")],
    ]
    await query.edit_message_text(
        f"👤 *Profilingiz*\n\n"
        f"📛 Ism: *{name}*\n"
        f"🆔 ID: `{user.id}`\n"
        f"👤 Username: {username}",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return ConversationHandler.END

async def back_menu_callback(update: Update, context):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    await query.edit_message_text(
        f"🎓 *Milliy Sertifikat Test Boti*\n\nTestga kirish uchun quyidagi tugmani bosing:",
        reply_markup=get_main_keyboard(user.id),
        parse_mode="Markdown"
    )

async def about_callback(update: Update, context):
    query = update.callback_query
    await query.answer()
    keyboard = [[InlineKeyboardButton("🔙 Orqaga", callback_data="back_menu")]]
    await query.edit_message_text(
        "ℹ️ *Bot haqida*\n\n"
        "🎓 Milliy sertifikat imtihoniga tayyorgarlik boti.\n\n"
        "📌 *Qanday ishlaydi:*\n"
        "1. Mini App'ni oching\n"
        "2. Test kodini kiriting\n"
        "3. Javoblarni bering\n"
        "4. Natija va sertifikat oling 🎉",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def admin_cmd(update: Update, context):
    user = update.effective_user
    if user.id != ADMIN_ID:
        await update.message.reply_text("❌ Ruxsat yo'q!")
        return
    admin_url = f"{RENDER_URL}/admin-app"
    keyboard = [[InlineKeyboardButton("👨‍💼 Admin panelni ochish", web_app=WebAppInfo(url=admin_url))]]
    await update.message.reply_text(
        "👨‍💼 *Admin Panel*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# ========== BOT + SERVER STARTUP ==========

def run_flask():
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

async def run_bot():
    global ptb_app, loop
    loop = asyncio.get_event_loop()
    await init_db()

    ptb_app = Application.builder().token(BOT_TOKEN).build()

    # Ism o'zgartirish conversation
    name_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(edit_name_callback, pattern="^edit_name$")],
        states={
            WAIT_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_new_name),
                CallbackQueryHandler(cancel_edit_callback, pattern="^cancel_edit$"),
            ]
        },
        fallbacks=[CallbackQueryHandler(cancel_edit_callback, pattern="^cancel_edit$")],
        allow_reentry=True,
        per_message=False,
    )

    ptb_app.add_handler(CommandHandler("start", start))
    ptb_app.add_handler(CommandHandler("admin", admin_cmd))
    ptb_app.add_handler(name_conv)
    ptb_app.add_handler(CallbackQueryHandler(check_sub_callback, pattern="^check_sub$"))
    ptb_app.add_handler(CallbackQueryHandler(profile_callback, pattern="^profile$"))
    ptb_app.add_handler(CallbackQueryHandler(back_menu_callback, pattern="^back_menu$"))
    ptb_app.add_handler(CallbackQueryHandler(about_callback, pattern="^about$"))

    await ptb_app.initialize()
    await ptb_app.start()

    if RENDER_URL:
        webhook_url = f"{RENDER_URL}/{BOT_TOKEN}"
        await ptb_app.bot.set_webhook(url=webhook_url, allowed_updates=["message", "callback_query"])
        logger.info(f"✅ Webhook: {webhook_url}")
        await ptb_app.bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(
                text="📝 Testga kirish",
                web_app=WebAppInfo(url=f"{RENDER_URL}/")
            )
        )
        logger.info("✅ Menu button o'rnatildi!")

    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logger.info("✅ Flask server ishga tushdi!")

    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(run_bot())

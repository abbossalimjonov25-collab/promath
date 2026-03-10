from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from config import ADMIN_ID
from database.db import (create_test, get_all_active_tests, end_test,
                          get_test_results, get_test)
from utils.test_checker import generate_test_code, parse_answers, answers_dict_to_string
from utils.pdf_generator import generate_results_pdf, generate_certificate
import io

# Conversation states
WAIT_ANSWERS, WAIT_SUBJECT, WAIT_END_CODE = range(3)

def is_admin(user_id):
    return user_id == ADMIN_ID

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin panel"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Sizda admin huquqi yo'q!")
        return

    keyboard = [
        [InlineKeyboardButton("➕ Yangi test yaratish", callback_data="admin_create_test")],
        [InlineKeyboardButton("📋 Faol testlar", callback_data="admin_active_tests")],
        [InlineKeyboardButton("🛑 Testni to'xtatish", callback_data="admin_end_test")],
    ]
    await update.message.reply_text(
        "👨‍💼 *Admin Panel*\n\nNimani amalga oshirmoqchisiz?",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin callback handler"""
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        await query.edit_message_text("❌ Ruxsat yo'q!")
        return

    if query.data == "admin_create_test":
        await query.edit_message_text(
            "📝 *Yangi test yaratish*\n\n"
            "Test kalitlarini quyidagi formatda yuboring:\n\n"
            "Format: `1A2B3C4D5A6B7C8D9A10B`\n\n"
            "Yoki: `ABCDABCDAB` (1dan boshlab)\n\n"
            "Misol: `1A2B3D4C5A6B7C8A9D10B`",
            parse_mode="Markdown"
        )
        return WAIT_ANSWERS

    elif query.data == "admin_active_tests":
        tests = await get_all_active_tests(query.from_user.id)
        if not tests:
            await query.edit_message_text("📭 Hozirda faol testlar yo'q.")
            return

        msg = "📋 *Faol testlar:*\n\n"
        for t in tests:
            msg += f"🔑 Kod: `{t['test_code']}`\n"
            msg += f"   Fan: {t['subject']}\n"
            msg += f"   Savollar: {t['total_questions']} ta\n"
            msg += f"   Yaratilgan: {t['created_at'].strftime('%d.%m.%Y %H:%M')}\n\n"
        await query.edit_message_text(msg, parse_mode="Markdown")

    elif query.data == "admin_end_test":
        tests = await get_all_active_tests(query.from_user.id)
        if not tests:
            await query.edit_message_text("📭 To'xtatish uchun faol test yo'q.")
            return

        keyboard = [[InlineKeyboardButton(
            f"🛑 {t['test_code']} ({t['subject']})",
            callback_data=f"end_{t['test_code']}"
        )] for t in tests]
        await query.edit_message_text(
            "Qaysi testni to'xtatmoqchisiz?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data.startswith("end_"):
        test_code = query.data[4:]
        await process_end_test(query, context, test_code)

async def receive_answers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Test kalitlarini qabul qilish"""
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END

    context.user_data['pending_answers'] = update.message.text.strip()

    parsed = parse_answers(update.message.text.strip())
    if not parsed:
        await update.message.reply_text(
            "❌ Format noto'g'ri! Qaytadan kiriting.\n\n"
            "Misol: `1A2B3C4D5A`",
            parse_mode="Markdown"
        )
        return WAIT_ANSWERS

    context.user_data['parsed_answers'] = parsed
    count = len(parsed)

    keyboard = [
        [InlineKeyboardButton("Matematika", callback_data="subj_Matematika")],
        [InlineKeyboardButton("Fizika", callback_data="subj_Fizika")],
        [InlineKeyboardButton("Kimyo", callback_data="subj_Kimyo")],
        [InlineKeyboardButton("Biologiya", callback_data="subj_Biologiya")],
        [InlineKeyboardButton("Ingliz tili", callback_data="subj_Ingliz_tili")],
    ]

    await update.message.reply_text(
        f"✅ *{count} ta savol kaliti qabul qilindi!*\n\nFanini tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return WAIT_SUBJECT

async def receive_subject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fan tanlash"""
    query = update.callback_query
    await query.answer()

    subject = query.data.replace("subj_", "").replace("_", " ")
    parsed_answers = context.user_data.get('parsed_answers', {})

    test_code = generate_test_code()
    answers_str = answers_dict_to_string(parsed_answers)

    await create_test(
        test_code=test_code,
        answers=answers_str,
        total_questions=len(parsed_answers),
        created_by=query.from_user.id,
        subject=subject
    )

    await query.edit_message_text(
        f"🎉 *Test muvaffaqiyatli yaratildi!*\n\n"
        f"🔑 *Test kodi:* `{test_code}`\n"
        f"📚 *Fan:* {subject}\n"
        f"📊 *Savollar soni:* {len(parsed_answers)} ta\n\n"
        f"Ushbu kodni o'quvchilarga ulashing.\n"
        f"O'quvchilar: `/test {test_code}` deb yuboring",
        parse_mode="Markdown"
    )
    return ConversationHandler.END

async def process_end_test(query, context, test_code):
    """Testni to'xtatish va natijalarni yuborish"""
    test = await get_test(test_code)

    # Faol testlar listida emas, barcha testdan ham qidiramiz
    from database.db import get_pool
    pool = await get_pool()
    async with pool.acquire() as conn:
        test_row = await conn.fetchrow("SELECT * FROM tests WHERE test_code=$1", test_code)

    if not test_row:
        await query.edit_message_text("❌ Test topilmadi!")
        return

    await end_test(test_code)
    results = await get_test_results(test_code)

    if not results:
        await query.edit_message_text(
            f"🛑 Test `{test_code}` to'xtatildi.\n\n📭 Hech kim test topshirmadi.",
            parse_mode="Markdown"
        )
        return

    # Admin uchun PDF natijalar
    pdf_buffer = generate_results_pdf(test_code, test_row['subject'], results)

    await query.edit_message_text(
        f"🛑 Test `{test_code}` to'xtatildi!\n"
        f"👥 Ishtirokchilar: {len(results)} ta\n\n"
        f"📊 Natijalar PDF tayyorlanmoqda...",
        parse_mode="Markdown"
    )

    # PDF yuborish
    await context.bot.send_document(
        chat_id=query.from_user.id,
        document=pdf_buffer,
        filename=f"natijalar_{test_code}.pdf",
        caption=f"📊 Test `{test_code}` natijalari\n👥 {len(results)} ta ishtirokchi",
        parse_mode="Markdown"
    )

    # Har bir o'quvchiga sertifikat yuborish
    await query.message.reply_text(
        f"📜 {len(results)} ta o'quvchiga sertifikat yuborilmoqda..."
    )

    for rank, row in enumerate(results, 1):
        try:
            cert_buffer = generate_certificate(
                user_name=row['full_name'] or f"Foydalanuvchi {row['user_id']}",
                subject=test_row['subject'],
                score=row['score'],
                total=row['total'],
                percentage=row['percentage'],
                test_code=test_code,
                rank=rank
            )
            await context.bot.send_document(
                chat_id=row['user_id'],
                document=cert_buffer,
                filename=f"sertifikat_{test_code}.pdf",
                caption=(
                    f"🎓 *Tabriklaymiz, {row['full_name'] or 'O\'quvchi'}!*\n\n"
                    f"📚 Fan: {test_row['subject']}\n"
                    f"✅ Natija: {row['score']}/{row['total']} ({row['percentage']:.1f}%)\n"
                    f"🏆 O'rin: {rank}-chi\n\n"
                    f"Sertifikatingiz tayyor! 🎉"
                ),
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"Sertifikat yuborishda xato {row['user_id']}: {e}")

    await query.message.reply_text(
        f"✅ Barcha sertifikatlar yuborildi!\n"
        f"📊 Test `{test_code}` yakunlandi.",
        parse_mode="Markdown"
    )

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Bekor qilindi.")
    return ConversationHandler.END

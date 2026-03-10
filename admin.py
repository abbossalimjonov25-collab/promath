from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
import os

from database.db import (create_test, get_all_active_tests, end_test,
                          get_test_results, get_test_any)
from utils.test_checker import generate_test_code, parse_answers, answers_dict_to_string
from utils.pdf_generator import generate_results_pdf, generate_certificate

WAIT_ANSWERS, WAIT_SUBJECT = range(2)

def is_admin(user_id):
    return user_id == int(os.getenv("ADMIN_ID", "0"))

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        await query.edit_message_text("❌ Ruxsat yo'q!")
        return

    if query.data == "admin_create_test":
        await query.edit_message_text(
            "📝 *Yangi test yaratish*\n\n"
            "Test kalitlarini yuboring:\n\n"
            "Format: `1A2B3C4D5A6B7C8D9A10B`\n\n"
            "Yoki faqat harflar: `ABCDABCDAB`",
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
            msg += f"   Fan: {t['subject']} | Savollar: {t['total_questions']} ta\n"
            msg += f"   Yaratilgan: {t['created_at'].strftime('%d.%m.%Y %H:%M')}\n\n"
        await query.edit_message_text(msg, parse_mode="Markdown")

    elif query.data == "admin_end_test":
        tests = await get_all_active_tests(query.from_user.id)
        if not tests:
            await query.edit_message_text("📭 To'xtatish uchun faol test yo'q.")
            return

        keyboard = [[InlineKeyboardButton(
            f"🛑 {t['test_code']} — {t['subject']}",
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
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END

    text = update.message.text.strip()
    parsed = parse_answers(text)

    if not parsed:
        # Faqat harflar formatini tekshirish
        letters = text.upper().replace(" ", "")
        if all(c.isalpha() for c in letters) and len(letters) > 0:
            parsed = {i+1: l for i, l in enumerate(letters)}
        else:
            await update.message.reply_text(
                "❌ Format noto'g'ri! Qaytadan kiriting.\n\nMisol: `1A2B3C4D5A`",
                parse_mode="Markdown"
            )
            return WAIT_ANSWERS

    context.user_data['parsed_answers'] = parsed

    keyboard = [
        [InlineKeyboardButton("📐 Matematika", callback_data="subj_Matematika")],
        [InlineKeyboardButton("⚡ Fizika", callback_data="subj_Fizika")],
        [InlineKeyboardButton("🧪 Kimyo", callback_data="subj_Kimyo")],
        [InlineKeyboardButton("🌿 Biologiya", callback_data="subj_Biologiya")],
        [InlineKeyboardButton("🌍 Ingliz tili", callback_data="subj_Ingliz_tili")],
        [InlineKeyboardButton("📖 Ona tili", callback_data="subj_Ona_tili")],
    ]
    await update.message.reply_text(
        f"✅ *{len(parsed)} ta savol kaliti qabul qilindi!*\n\nFanini tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return WAIT_SUBJECT

async def receive_subject(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        f"O'quvchilar quyidagini yuboring:\n"
        f"`/test {test_code}`",
        parse_mode="Markdown"
    )
    context.user_data.clear()
    return ConversationHandler.END

async def process_end_test(query, context, test_code):
    test_row = await get_test_any(test_code)

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

    await query.edit_message_text(
        f"🛑 Test `{test_code}` to'xtatildi!\n"
        f"👥 Ishtirokchilar: {len(results)} ta\n\n"
        f"⏳ PDF natijalar tayyorlanmoqda...",
        parse_mode="Markdown"
    )

    # Admin uchun PDF
    pdf_buffer = generate_results_pdf(test_code, test_row['subject'], results)
    await context.bot.send_document(
        chat_id=query.from_user.id,
        document=pdf_buffer,
        filename=f"natijalar_{test_code}.pdf",
        caption=f"📊 Test `{test_code}` natijalari — {len(results)} ta ishtirokchi",
        parse_mode="Markdown"
    )

    await query.message.reply_text(f"📜 {len(results)} ta o'quvchiga sertifikat yuborilmoqda...")

    # Har bir o'quvchiga sertifikat
    for rank, row in enumerate(results, 1):
        try:
            cert_buffer = generate_certificate(
                user_name=row['full_name'] or f"O'quvchi {row['user_id']}",
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

    await query.message.reply_text("✅ Barcha sertifikatlar yuborildi!")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("❌ Bekor qilindi.")
    return ConversationHandler.END

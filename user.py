from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMember
from telegram.ext import ContextTypes, ConversationHandler
import os

from database.db import (register_user, get_test, submit_answers, check_already_submitted)
from utils.test_checker import parse_answers, check_answers, format_detailed_result

WAIT_TEST_CODE, WAIT_USER_ANSWERS = range(10, 12)

async def check_subscription(bot, user_id) -> bool:
    channel_id = os.getenv("CHANNEL_ID")
    if not channel_id:
        return True
    try:
        member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
        return member.status in [
            ChatMember.MEMBER,
            ChatMember.ADMINISTRATOR,
            ChatMember.OWNER
        ]
    except Exception as e:
        print(f"Obuna tekshirishda xato: {e}")
        return True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await register_user(user.id, user.full_name, user.username)

    is_subscribed = await check_subscription(context.bot, user.id)

    if not is_subscribed:
        channel_username = os.getenv("CHANNEL_USERNAME", "")
        channel_link = f"https://t.me/{channel_username.lstrip('@')}" if channel_username else "https://t.me"
        keyboard = [
            [InlineKeyboardButton("📢 Kanalga obuna bo'lish", url=channel_link)],
            [InlineKeyboardButton("✅ Obunani tekshirish", callback_data="check_sub")]
        ]
        await update.message.reply_text(
            f"👋 Salom, *{user.first_name}*!\n\n"
            f"⚠️ Botdan foydalanish uchun avval kanalimizga obuna bo'ling!\n\n"
            f"Obuna bo'lgandan so'ng ✅ tugmasini bosing.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return

    await show_main_menu(update, context)

async def check_sub_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user

    is_subscribed = await check_subscription(context.bot, user.id)
    if not is_subscribed:
        channel_username = os.getenv("CHANNEL_USERNAME", "")
        channel_link = f"https://t.me/{channel_username.lstrip('@')}" if channel_username else "https://t.me"
        keyboard = [
            [InlineKeyboardButton("📢 Kanalga obuna bo'lish", url=channel_link)],
            [InlineKeyboardButton("✅ Obunani tekshirish", callback_data="check_sub")]
        ]
        await query.edit_message_text(
            "❌ Siz hali kanalga obuna bo'lmadingiz!\n\nIltimos, avval obuna bo'ling.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    await register_user(user.id, user.full_name, user.username)
    await query.edit_message_text("✅ Obuna tasdiqlandi! Xush kelibsiz!")
    await show_main_menu_message(query.message, user, context)

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    admin_id = int(os.getenv("ADMIN_ID", "0"))

    keyboard = [
        [InlineKeyboardButton("📝 Testga kirish", callback_data="enter_test")],
        [InlineKeyboardButton("ℹ️ Bot haqida", callback_data="about")],
    ]
    if user.id == admin_id:
        keyboard.insert(0, [InlineKeyboardButton("👨‍💼 Admin panel", callback_data="go_admin")])

    await update.message.reply_text(
        f"🎉 Xush kelibsiz, *{user.first_name}*!\n\n"
        f"🎓 *Milliy Sertifikat Test Boti*\n\n"
        f"✅ Test ishlash\n"
        f"📊 Natijalarni ko'rish\n"
        f"🏆 Sertifikat olish\n\n"
        f"Quyidagi tugmani tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def show_main_menu_message(message, user, context):
    admin_id = int(os.getenv("ADMIN_ID", "0"))
    keyboard = [
        [InlineKeyboardButton("📝 Testga kirish", callback_data="enter_test")],
        [InlineKeyboardButton("ℹ️ Bot haqida", callback_data="about")],
    ]
    if user.id == admin_id:
        keyboard.insert(0, [InlineKeyboardButton("👨‍💼 Admin panel", callback_data="go_admin")])

    await message.reply_text(
        f"🎉 Xush kelibsiz, *{user.first_name}*!\n\nQuyidagi tugmani tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "enter_test":
        await query.edit_message_text(
            "📝 *Testga kirish*\n\n"
            "Test kodini yuboring:\n"
            "Misol: `ABC123`",
            parse_mode="Markdown"
        )
        return WAIT_TEST_CODE

    elif query.data == "about":
        await query.edit_message_text(
            "ℹ️ *Bot haqida*\n\n"
            "🎓 Milliy sertifikat imtihoniga tayyorgarlik boti.\n\n"
            "📌 *Qanday ishlaydi:*\n"
            "1. Test kodini oling\n"
            "2. Botga `/test KOD` yuboring\n"
            "3. Javoblaringizni kiriting\n"
            "4. Natija va sertifikat oling 🎉",
            parse_mode="Markdown"
        )

    elif query.data == "go_admin":
        from handlers.admin import admin_panel
        await query.message.reply_text("Admin panel:")
        # Admin panel ni chaqirish uchun fake update
        class FakeUpdate:
            effective_user = query.from_user
            message = query.message
        await admin_panel(FakeUpdate(), context)

async def enter_test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    is_subscribed = await check_subscription(context.bot, user.id)
    if not is_subscribed:
        await update.message.reply_text("⚠️ Avval kanalga obuna bo'ling! /start")
        return ConversationHandler.END

    if context.args:
        test_code = context.args[0].upper()
        return await process_test_code(update, context, test_code)

    await update.message.reply_text(
        "📝 Test kodini yuboring:\n\nMisol: `ABC123`",
        parse_mode="Markdown"
    )
    return WAIT_TEST_CODE

async def receive_test_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    test_code = update.message.text.strip().upper()
    return await process_test_code(update, context, test_code)

async def process_test_code(update: Update, context: ContextTypes.DEFAULT_TYPE, test_code: str):
    user_id = update.effective_user.id
    test = await get_test(test_code)

    if not test:
        await update.message.reply_text(
            f"❌ `{test_code}` kodli faol test topilmadi!\n\n"
            "Test kodi noto'g'ri yoki test yakunlangan.",
            parse_mode="Markdown"
        )
        return WAIT_TEST_CODE

    already = await check_already_submitted(test_code, user_id)
    if already:
        await update.message.reply_text(
            f"⚠️ Siz `{test_code}` testini allaqachon topshirgansiz!\n\n"
            "Har bir test faqat bir marta topshiriladi.",
            parse_mode="Markdown"
        )
        return ConversationHandler.END

    context.user_data['current_test_code'] = test_code
    context.user_data['current_test'] = dict(test)

    await update.message.reply_text(
        f"✅ *Test topildi!*\n\n"
        f"📚 Fan: *{test['subject']}*\n"
        f"🔑 Kod: `{test_code}`\n"
        f"📊 Savollar: *{test['total_questions']} ta*\n\n"
        f"Javoblarni yuboring:\n"
        f"Format: `1A2B3C4D5A` yoki `ABCDA...`",
        parse_mode="Markdown"
    )
    return WAIT_USER_ANSWERS

async def receive_user_answers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_answers_text = update.message.text.strip()

    test_code = context.user_data.get('current_test_code')
    test = context.user_data.get('current_test')

    if not test_code or not test:
        await update.message.reply_text("❌ Xato yuz berdi. /start buyrug'ini yuboring.")
        return ConversationHandler.END

    correct_answers = parse_answers(test['answers'])
    score, total, percentage, detailed = check_answers(correct_answers, user_answers_text)

    await submit_answers(
        test_code=test_code,
        user_id=user.id,
        user_answers=user_answers_text,
        score=score,
        total=total,
        percentage=percentage
    )

    if percentage >= 85:
        emoji, grade = "🥇", "A'LO"
        msg_extra = "Ajoyib natija! Sertifikatingizni kuting. 🎉"
    elif percentage >= 70:
        emoji, grade = "🥈", "YAXSHI"
        msg_extra = "Yaxshi natija! Sertifikatingizni kuting. 👏"
    elif percentage >= 55:
        emoji, grade = "🥉", "QONIQARLI"
        msg_extra = "Sertifikatingizni kuting. 💪"
    else:
        emoji, grade = "📝", "QATNASHDI"
        msg_extra = "Keyingi safar ko'proq tayyorlaning! 📚"

    detail_text = format_detailed_result(detailed, max_show=10)

    await update.message.reply_text(
        f"{emoji} *Test natijasi*\n\n"
        f"📚 Fan: {test['subject']}\n"
        f"🔑 Kod: `{test_code}`\n\n"
        f"✅ To'g'ri javoblar: *{score}/{total}*\n"
        f"📊 Foiz: *{percentage:.1f}%*\n"
        f"🏅 Baho: *{grade}*\n\n"
        f"📋 *Javoblar tahlili:*\n"
        f"{detail_text}\n\n"
        f"💬 {msg_extra}",
        parse_mode="Markdown"
    )

    context.user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("❌ Bekor qilindi. /start")
    return ConversationHandler.END

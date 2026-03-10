from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMember
from telegram.ext import ContextTypes, ConversationHandler
from config import CHANNEL_ID, CHANNEL_USERNAME, ADMIN_ID
from database.db import (register_user, get_test, submit_answers,
                          check_already_submitted)
from utils.test_checker import parse_answers, check_answers, format_detailed_result

# Conversation states
WAIT_TEST_CODE, WAIT_USER_ANSWERS = range(10, 12)

async def check_subscription(bot, user_id) -> bool:
    """Kanal obunasini tekshirish"""
    if not CHANNEL_ID:
        return True
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in [
            ChatMember.MEMBER,
            ChatMember.ADMINISTRATOR,
            ChatMember.OWNER
        ]
    except Exception as e:
        print(f"Obuna tekshirishda xato: {e}")
        return True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start komandasi"""
    user = update.effective_user

    # Foydalanuvchini DBga saqlash
    await register_user(
        user_id=user.id,
        full_name=user.full_name,
        username=user.username
    )

    # Obuna tekshirish
    is_subscribed = await check_subscription(context.bot, user.id)

    if not is_subscribed:
        channel_link = f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}" if CHANNEL_USERNAME else "#"
        keyboard = [
            [InlineKeyboardButton("📢 Kanalga obuna bo'lish", url=channel_link)],
            [InlineKeyboardButton("✅ Obunani tekshirish", callback_data="check_sub")]
        ]
        await update.message.reply_text(
            f"👋 Salom, *{user.first_name}*!\n\n"
            f"⚠️ Botdan foydalanish uchun avval kanalimizga obuna bo'ling:\n\n"
            f"📢 {CHANNEL_USERNAME or 'Kanalimiz'}\n\n"
            f"Obuna bo'lgandan so'ng ✅ tugmasini bosing.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return

    await show_main_menu(update, context, user.first_name)

async def check_sub_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Obunani qayta tekshirish"""
    query = update.callback_query
    await query.answer()

    user = query.from_user
    is_subscribed = await check_subscription(context.bot, user.id)

    if not is_subscribed:
        channel_link = f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}" if CHANNEL_USERNAME else "#"
        keyboard = [
            [InlineKeyboardButton("📢 Kanalga obuna bo'lish", url=channel_link)],
            [InlineKeyboardButton("✅ Obunani tekshirish", callback_data="check_sub")]
        ]
        await query.edit_message_text(
            "❌ Siz hali kanalga obuna bo'lmadingiz!\n\n"
            "Iltimos, avval kanalga obuna bo'ling va qaytadan tekshiring.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    await register_user(user.id, user.full_name, user.username)
    await query.edit_message_text("✅ Obuna tasdiqlandi!")
    await show_main_menu_from_query(query, context, user.first_name)

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, name: str):
    """Asosiy menyu"""
    keyboard = [
        [InlineKeyboardButton("📝 Testga kirish", callback_data="enter_test")],
        [InlineKeyboardButton("ℹ️ Bot haqida", callback_data="about")],
    ]
    if update.effective_user.id == ADMIN_ID:
        keyboard.insert(0, [InlineKeyboardButton("👨‍💼 Admin panel", callback_data="admin_main")])

    await update.message.reply_text(
        f"🎉 Xush kelibsiz, *{name}*!\n\n"
        f"🎓 *Milliy Sertifikat Test Boti*\n\n"
        f"Bu bot orqali siz:\n"
        f"✅ Matematika testlarini ishlashingiz\n"
        f"📊 Natijalaringizni bilishingiz\n"
        f"🏆 Sertifikat olishingiz mumkin!\n\n"
        f"Boshlash uchun quyidagi tugmalardan birini tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def show_main_menu_from_query(query, context, name: str):
    """Query dan asosiy menyu"""
    keyboard = [
        [InlineKeyboardButton("📝 Testga kirish", callback_data="enter_test")],
        [InlineKeyboardButton("ℹ️ Bot haqida", callback_data="about")],
    ]
    if query.from_user.id == ADMIN_ID:
        keyboard.insert(0, [InlineKeyboardButton("👨‍💼 Admin panel", callback_data="admin_main")])

    await query.message.reply_text(
        f"🎉 Xush kelibsiz, *{name}*!\n\n"
        f"🎓 *Milliy Sertifikat Test Boti*\n\n"
        f"Boshlash uchun tugmani tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menyu callback handleri"""
    query = update.callback_query
    await query.answer()

    if query.data == "enter_test":
        await query.edit_message_text(
            "📝 *Testga kirish*\n\n"
            "Test kodini yuboring:\n"
            "Misol: `/test ABC123`\n\n"
            "Yoki to'g'ridan-to'g'ri test kodini yozing:",
            parse_mode="Markdown"
        )
        return WAIT_TEST_CODE

    elif query.data == "about":
        await query.edit_message_text(
            "ℹ️ *Bot haqida*\n\n"
            "🎓 Bu bot milliy sertifikat imtihoniga tayyorgarlik uchun mo'ljallangan.\n\n"
            "📌 *Qanday ishlaydi:*\n"
            "1. Test kodini oling\n"
            "2. Botga kod yuboring\n"
            "3. Javoblaringizni kiriting\n"
            "4. Natijangiz va sertifikatingizni oling\n\n"
            "👨‍🏫 O'qituvchilar test yaratib, natijalarni PDF ko'rinishida olishlari mumkin.",
            parse_mode="Markdown"
        )

async def enter_test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/test komandasi"""
    user = update.effective_user
    is_subscribed = await check_subscription(context.bot, user.id)
    if not is_subscribed:
        await update.message.reply_text(
            "⚠️ Avval kanalga obuna bo'ling!\n/start buyrug'ini yuboring."
        )
        return ConversationHandler.END

    args = context.args
    if args:
        test_code = args[0].upper()
        return await process_test_code(update, context, test_code)

    await update.message.reply_text(
        "📝 Test kodini yuboring:\n\nMisol: `ABC123`",
        parse_mode="Markdown"
    )
    return WAIT_TEST_CODE

async def receive_test_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Test kodini qabul qilish"""
    test_code = update.message.text.strip().upper()
    return await process_test_code(update, context, test_code)

async def process_test_code(update: Update, context: ContextTypes.DEFAULT_TYPE, test_code: str):
    """Test kodini tekshirish"""
    user_id = update.effective_user.id
    test = await get_test(test_code)

    if not test:
        await update.message.reply_text(
            f"❌ `{test_code}` kodli faol test topilmadi!\n\n"
            "Test kodi noto'g'ri yoki test yakunlangan bo'lishi mumkin.\n"
            "Qaytadan tekshiring.",
            parse_mode="Markdown"
        )
        return WAIT_TEST_CODE

    # Allaqachon topshirganmi
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
        f"📊 Savollar soni: *{test['total_questions']} ta*\n\n"
        f"Javoblaringizni quyidagi formatda yuboring:\n\n"
        f"Format: `1A2B3C4D5A` (raqam + harf)\n"
        f"Yoki: `ABCDA...` (faqat harflar, 1dan boshlab)\n\n"
        f"⏰ Javoblaringizni yuboring:",
        parse_mode="Markdown"
    )
    return WAIT_USER_ANSWERS

async def receive_user_answers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Foydalanuvchi javoblarini qabul qilish va tekshirish"""
    user = update.effective_user
    user_answers_text = update.message.text.strip()

    test_code = context.user_data.get('current_test_code')
    test = context.user_data.get('current_test')

    if not test_code or not test:
        await update.message.reply_text("❌ Xato yuz berdi. /start buyrug'ini yuboring.")
        return ConversationHandler.END

    # Tekshirish
    from utils.test_checker import parse_answers, check_answers, format_detailed_result
    correct_answers = parse_answers(test['answers'])
    score, total, percentage, detailed = check_answers(correct_answers, user_answers_text)

    # DBga saqlash
    await submit_answers(
        test_code=test_code,
        user_id=user.id,
        user_answers=user_answers_text,
        score=score,
        total=total,
        percentage=percentage
    )

    # Natija emoji
    if percentage >= 85:
        emoji = "🥇"
        grade = "A'LO"
        msg_extra = "Zo'r natija! Sertifikatingiz test yakunlangach yuboriladi. 🎉"
    elif percentage >= 70:
        emoji = "🥈"
        grade = "YAXSHI"
        msg_extra = "Yaxshi natija! Sertifikatingizni kuting. 👏"
    elif percentage >= 55:
        emoji = "🥉"
        grade = "QONIQARLI"
        msg_extra = "Yaxshi harakat! Sertifikatingizni kuting. 💪"
    else:
        emoji = "📝"
        grade = "QATNASHDI"
        msg_extra = "Keyingi safar ko'proq tayyorlaning! Sertifikat kuting. 📚"

    # Batafsil natija (birinchi 10 ta)
    detail_text = format_detailed_result(detailed, max_show=10)

    await update.message.reply_text(
        f"{emoji} *Test natijasi*\n\n"
        f"📚 Fan: {test['subject']}\n"
        f"🔑 Kod: `{test_code}`\n\n"
        f"✅ To'g'ri javoblar: *{score}/{total}*\n"
        f"📊 Foiz: *{percentage:.1f}%*\n"
        f"🏅 Baho: *{grade}*\n\n"
        f"📋 *Javoblar tahlili (birinchi 10):*\n"
        f"{detail_text}\n\n"
        f"💬 {msg_extra}",
        parse_mode="Markdown"
    )

    context.user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Bekor qilindi. /start")
    context.user_data.clear()
    return ConversationHandler.END

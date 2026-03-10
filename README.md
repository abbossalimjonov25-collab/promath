# 🎓 Milliy Sertifikat Test Boti

Matematikadan milliy sertifikat tayyorlov uchun Telegram bot.

## 📋 Funksiyalar

- ✅ Majburiy kanal obunasi
- 👨‍💼 Admin: test kalitlarini kiritish → avtomatik kod berish
- 📝 O'quvchi: kod orqali testga kirish va javob yuborish
- 📊 Test yakunida PDF natijalar (admin uchun)
- 🎓 Har bir o'quvchiga avtomatik sertifikat

---

## ⚙️ O'rnatish

### 1. Bot yaratish
1. Telegram'da [@BotFather](https://t.me/BotFather) ga yozing
2. `/newbot` buyrug'ini yuboring
3. Bot nomini va username'ni kiriting
4. **TOKEN** ni saqlang

### 2. Admin ID olish
1. [@userinfobot](https://t.me/userinfobot) ga `/start` yuboring
2. **ID** raqamingizni saqlang

### 3. Kanal sozlash
1. Telegram kanalini yarating
2. Botni kanal adminligiga qo'shing
3. Kanal ID sini oling:
   - [@username_to_id_bot](https://t.me/username_to_id_bot) dan foydalaning

### 4. Neon Database
1. [neon.tech](https://neon.tech) ga kiring
2. Yangi project yarating
3. **Connection string** ni saqlang (postgresql://...)

---

## 🚀 Render.com ga Deploy qilish

### 1. GitHub'ga yuklash
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/username/math-bot.git
git push -u origin main
```

### 2. Render'da yaratish
1. [render.com](https://render.com) ga kiring
2. **New → Background Worker** tanlang
3. GitHub reponi ulang
4. Quyidagi sozlamalarni kiriting:

| Sozlama | Qiymat |
|---------|--------|
| Build Command | `pip install -r requirements.txt` |
| Start Command | `python bot.py` |

### 3. Environment Variables (Render dashboard'da)
```
BOT_TOKEN         = your_bot_token
DATABASE_URL      = postgresql://...
ADMIN_ID          = 123456789
CHANNEL_ID        = -1001234567890
CHANNEL_USERNAME  = @mening_kanalim
```

---

## ⏰ Cron-job.org (Render Free Tier uchun)

Render free tier 15 daqiqada "uyquga ketadi". Shuning uchun:

1. [cron-job.org](https://cron-job.org) ga kiring (bepul)
2. Yangi cron job yarating:
   - **URL**: `https://your-service.onrender.com/` *(yoki ping URL)*
   - **Schedule**: `*/10 * * * *` (har 10 daqiqada)

> **Muhim:** Render Worker service'larda HTTP endpoint yo'q.
> Shuning uchun cron-job bot'ni "uyg'otmaydi" - lekin botni **Worker** sifatida deploy qilsangiz, u doim ishlaydi (free tier'da ham).
> Agar xavotir olsangiz, cron-job.org'da render dashboard URL'ini ping qiling.

---

## 📱 Foydalanish

### Admin uchun:
1. `/admin` → Admin panel
2. **Yangi test yaratish** → kalitlarni kiriting (`1A2B3C4D5A`)
3. Fan tanlang → **Test kodi** avtomatik beriladi
4. Kodni o'quvchilarga ulashing
5. Test yakunida **Testni to'xtatish** → PDF + sertifikatlar yuboriladi

### O'quvchi uchun:
1. `/start` → Kanalga obuna bo'lish
2. `/test KOD123` → Test kodini kiriting
3. Javoblarni yuboring: `1A2B3C4D5A` yoki `ABCDA`
4. Natijani ko'ring
5. Test yakunlangach sertifikat oling

---

## 📁 Fayl strukturasi
```
math_bot/
├── bot.py              # Asosiy bot fayli
├── config.py           # Konfiguratsiya
├── requirements.txt    # Kutubxonalar
├── render.yaml         # Render config
├── .env.example        # ENV o'rnak
├── database/
│   ├── __init__.py
│   └── db.py           # PostgreSQL (Neon)
├── handlers/
│   ├── __init__.py
│   ├── admin.py        # Admin funksiyalar
│   └── user.py         # Foydalanuvchi funksiyalar
└── utils/
    ├── __init__.py
    ├── test_checker.py  # Javob tekshirish
    └── pdf_generator.py # PDF va sertifikat
```

---

## 🎨 Test kalitlari formatlari

Barcha formatlar qabul qilinadi:
```
1A2B3C4D5A6B        ✅
ABCDABCD             ✅
1-A 2-B 3-C 4-D     ✅
```

---

## ❓ Muammolar

**Bot ishlamayapti?**
- `.env` faylni tekshiring
- Bot kanalda admin ekanligini tekshiring
- Database URL to'g'riligini tekshiring

**Neon DB ulanmaydi?**
- `ssl=require` parametri tekshirilsin
- IP allowlist tekshirilsin (Neon'da barcha IP uchun ochiq qiling)

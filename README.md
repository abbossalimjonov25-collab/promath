# 🎓 Milliy Sertifikat — Matematika Tayyorlov Boti

Telegram bot — Milliy Sertifikat matematika imtihoniga tayyorlanish uchun.

---

## 📁 Loyiha tuzilmasi

```
milliy_sertifikat_bot/
├── bot.py                  # Asosiy ishga tushirish fayli
├── config.py               # Sozlamalar (env o'zgaruvchilar)
├── health.py               # Health check (cron-job uchun)
├── requirements.txt        # Python kutubxonalari
├── render.yaml             # Render.com deploy konfiguratsiyasi
├── .env.example            # Muhit o'zgaruvchilari namunasi
├── .gitignore
├── database/
│   ├── __init__.py
│   └── db.py               # PostgreSQL so'rovlari
├── handlers/
│   ├── __init__.py
│   ├── start.py            # /start, ma'lumot
│   ├── profile.py          # Profil, ism o'zgartirish
│   ├── test.py             # Test o'tkazish logikasi
│   ├── stats.py            # Statistika
│   ├── leaderboard.py      # Top-10 reyting
│   └── admin.py            # Admin panel
└── utils/
    ├── __init__.py
    └── keyboards.py        # Barcha tugmalar
```

---

## 🚀 O'rnatish va ishga tushirish

### 1. GitHub — Repozitoriy yaratish

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/SIZNING_USERNAME/milliy-sertifikat-bot.git
git push -u origin main
```

### 2. Neon PostgreSQL — Database yaratish

1. [neon.tech](https://neon.tech) ga o'ting va ro'yxatdan o'ting
2. **New Project** → nom kiriting (masalan: `milliy-sertifikat`)
3. Region: **Europe (Frankfurt)** yoki yaqin region tanlang
4. **Dashboard → Connection Details** → **Connection string** ni nusxalang
5. Format: `postgresql://user:password@ep-xxx.aws.neon.tech/neondb?sslmode=require`

> ✅ Jadvallar bot birinchi ishga tushganda **avtomatik yaratiladi** (`init_db()`)

### 3. Render.com — Deploy qilish

1. [render.com](https://render.com) ga kiring
2. **New → Background Worker** tanlang
3. GitHub reponi ulang
4. Sozlamalar:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python bot.py`
5. **Environment Variables** qo'shing:

| Key | Value |
|-----|-------|
| `BOT_TOKEN` | BotFather dan olgan token |
| `DATABASE_URL` | Neon connection string |
| `ADMIN_IDS` | Sizning Telegram ID (masalan: `123456789`) |

6. **Deploy** tugmasini bosing

### 4. Cron-job.org — Botni uyg'otib turish

> Render.com bepul tariffda **15 daqiqada** xizmatni to'xtatadi.
> Cron-job.org har 14 daqiqada ping yuboradi.

1. [cron-job.org](https://cron-job.org) ga kiring
2. **Create Cronjob** → URL: `https://SIZNING-BOT.onrender.com/health`
3. Interval: **Every 14 minutes**
4. Saqlang ✅

> **Eslatma:** Worker rejimida health endpoint ishlamaydi.
> Render.com da **Web Service** sifatida deploy qilsangiz, `health.py` ni `bot.py` ga ulang.

---

## 🤖 Bot buyruqlari

| Buyruq | Vazifa |
|--------|--------|
| `/start` | Botni ishga tushirish |
| `/rename` | Ismni o'zgartirish |
| `/del_q 5` | 5-savolni o'chirish (admin) |
| `/cancel` | Joriy amalni bekor qilish |

---

## ⚙️ Admin panel

1. `ADMIN_IDS` ga o'z Telegram ID ingizni qo'shing
2. Bot da **⚙️ Admin panel** tugmasi paydo bo'ladi
3. Savollar qo'shish:
   - **Test (MCQ):** savol + 4 variant + to'g'ri javob + izoh
   - **Ochiq savol:** savol + aniq javob + izoh

---

## 📊 Funksiyalar

- ✅ Aralash format: 7 MCQ + 3 ochiq savol
- ✅ Natija va ball ko'rsatish
- ✅ O'rtacha, eng yuqori ball statistikasi
- ✅ Top-10 reyting jadvali
- ✅ Profil sahifasi
- ✅ Ism o'zgartirish
- ✅ Admin: savol qo'shish/o'chirish
- ✅ Admin: bot statistikasi

---

## 🔧 Mahalliy ishga tushirish

```bash
# Virtual muhit
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Kutubxonalar
pip install -r requirements.txt

# .env fayl
cp .env.example .env
# .env faylni o'zingiznikiga to'ldiring

# Ishga tushirish
python bot.py
```

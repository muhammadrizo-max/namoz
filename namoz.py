import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import sqlite3
from datetime import datetime
import requests
import json

# Logging sozlamalari
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot tokeni
BOT_TOKEN = "8577362508:AAGMm5nF5aBvkPsekGgMmfXe21Ug6kLgwCA"

# Bot versiyasi
BOT_VERSION = "v1.0"

# Admin ID
ADMIN_IDS = [6582564319]  # Admin Telegram IDlarini kiriting

# Majburiy obuna kanallari
CHANNELS = {}  # Admin panel orqali qo'shiladi

# O'zbekiston hududlari
REGIONS = {
    "tashkent": "Toshkent",
    "samarkand": "Samarqand",
    "bukhara": "Buxoro",
    "andijan": "Andijon",
    "fergana": "Farg'ona",
    "namangan": "Namangan",
    "kashkadarya": "Qashqadaryo",
    "surkhandarya": "Surxondaryo",
    "jizzakh": "Jizzax",
    "syrdarya": "Sirdaryo",
    "navoi": "Navoiy",
    "khorezm": "Xorazm",
    "karakalpakstan": "Qoraqalpog'iston"
}

# Qur'on suralari
SURAHS = {
    1: "Al-Fotiha", 2: "Al-Baqara", 3: "Oli Imron", 4: "An-Niso", 5: "Al-Moida",
    6: "Al-An'om", 7: "Al-A'rof", 8: "Al-Anfol", 9: "At-Tavba", 10: "Yunus",
    11: "Hud", 12: "Yusuf", 13: "Ar-Ra'd", 14: "Ibrohim", 15: "Al-Hijr",
    16: "An-Nahl", 17: "Al-Isro", 18: "Al-Kahf", 19: "Maryam", 20: "Toha",
    21: "Al-Anbiyo", 22: "Al-Haj", 23: "Al-Mu'minun", 24: "An-Nur", 25: "Al-Furqon",
    26: "Ash-Shu'aro", 27: "An-Naml", 28: "Al-Qasas", 29: "Al-Ankabut", 30: "Ar-Rum",
    31: "Luqmon", 32: "As-Sajda", 33: "Al-Ahzob", 34: "Saba'", 35: "Fotir",
    36: "Yosin", 37: "As-Soffot", 38: "Sod", 39: "Az-Zumar", 40: "G'ofir",
    41: "Fussilat", 42: "Ash-Shuro", 43: "Az-Zuxruf", 44: "Ad-Duxon", 45: "Al-Josiya",
    46: "Al-Ahqof", 47: "Muhammad", 48: "Al-Fath", 49: "Al-Hujurot", 50: "Qof",
    51: "Az-Zoriyot", 52: "At-Tur", 53: "An-Najm", 54: "Al-Qamar", 55: "Ar-Rahmon",
    56: "Al-Voqi'a", 57: "Al-Hadid", 58: "Al-Mujodala", 59: "Al-Hashr", 60: "Al-Mumtahana",
    61: "As-Sof", 62: "Al-Jumu'a", 63: "Al-Munofiqun", 64: "At-Tag'obun", 65: "At-Taloq",
    66: "At-Tahrim", 67: "Al-Mulk", 68: "Al-Qalam", 69: "Al-Haqqa", 70: "Al-Ma'orij",
    71: "Nuh", 72: "Al-Jin", 73: "Al-Muzzammil", 74: "Al-Muddassir", 75: "Al-Qiyoma",
    76: "Al-Inson", 77: "Al-Mursalot", 78: "An-Naba'", 79: "An-Nozi'ot", 80: "Abasa",
    81: "At-Takvir", 82: "Al-Infitor", 83: "Al-Mutaffifin", 84: "Al-Inshiqoq", 85: "Al-Buruj",
    86: "At-Toriq", 87: "Al-A'lo", 88: "Al-G'oshiya", 89: "Al-Fajr", 90: "Al-Balad",
    91: "Ash-Shams", 92: "Al-Layl", 93: "Ad-Duho", 94: "Ash-Sharh", 95: "At-Tin",
    96: "Al-Alaq", 97: "Al-Qadr", 98: "Al-Bayyina", 99: "Az-Zalzala", 100: "Al-Odiyot",
    101: "Al-Qori'a", 102: "At-Takosur", 103: "Al-Asr", 104: "Al-Humaza", 105: "Al-Fil",
    106: "Quraysh", 107: "Al-Mo'un", 108: "Al-Kavsar", 109: "Al-Kofirun", 110: "An-Nasr",
    111: "Al-Masad", 112: "Al-Ixlos", 113: "Al-Falaq", 114: "An-Nos"
}

# Ma'lumotlar bazasi
def init_db():
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY, region TEXT, created_at TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS channels
                 (channel_id TEXT PRIMARY KEY, channel_name TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS duolar
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, content TEXT)''')
    conn.commit()
    conn.close()

# Foydalanuvchi obuna bo'lganligini tekshirish
async def check_subscription(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("SELECT channel_id FROM channels")
    channels = c.fetchall()
    conn.close()

    for channel in channels:
        try:
            member = await context.bot.get_chat_member(channel[0], user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                return False
        except:
            continue
    return True

# Obuna tugmalarini yaratish
async def get_subscription_keyboard():
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("SELECT channel_id, channel_name FROM channels")
    channels = c.fetchall()
    conn.close()

    keyboard = []
    for channel in channels:
        keyboard.append([InlineKeyboardButton(f"📢 {channel[1]}", url=f"https://t.me/{channel[0].replace('@', '')}")])
    keyboard.append([InlineKeyboardButton("✅ Tekshirish", callback_data="check_subscription")])
    return InlineKeyboardMarkup(keyboard)

# Start komandasi
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Admin tugmasi
    if user_id in ADMIN_IDS:
        admin_keyboard = ReplyKeyboardMarkup(
            [[KeyboardButton("👨‍💼 Admin Panel")]],
            resize_keyboard=True
        )
        context.bot_data['admin_keyboard'] = admin_keyboard

    # Obunani tekshirish
    if not await check_subscription(user_id, context):
        keyboard = await get_subscription_keyboard()
        await update.message.reply_text(
            "🔔 Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling:",
            reply_markup=keyboard
        )
        return

    # Hudud tanlash
    keyboard = []
    row = []
    for key, value in REGIONS.items():
        row.append(InlineKeyboardButton(value, callback_data=f"region_{key}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    reply_markup = InlineKeyboardMarkup(keyboard)

    if user_id in ADMIN_IDS:
        await update.message.reply_text(
            f"🕌 Assalomu alaykum!\n\n"
            f"Namoz vaqtlarini ko'rish uchun hududingizni tanlang:\n\n"
            f"🤖 Bot versiyasi: {BOT_VERSION}",
            reply_markup=reply_markup
        )
        await update.message.reply_text(
            "👨‍💼 Admin panel pastdagi tugmadan ochiladi",
            reply_markup=context.bot_data.get('admin_keyboard')
        )
    else:
        await update.message.reply_text(
            f"🕌 Assalomu alaykum!\n\n"
            f"Namoz vaqtlarini ko'rish uchun hududingizni tanlang:\n\n"
            f"🤖 Bot versiyasi: {BOT_VERSION}",
            reply_markup=reply_markup
        )

# Callback handler
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    # Obunani tekshirish
    if query.data == "check_subscription":
        if await check_subscription(user_id, context):
            await query.edit_message_text("✅ Obuna tasdiqlandi! /start buyrug'ini yuboring.")
        else:
            await query.answer("❌ Siz hali barcha kanallarga obuna bo'lmadingiz!", show_alert=True)
        return

    if not await check_subscription(user_id, context):
        keyboard = await get_subscription_keyboard()
        await query.edit_message_text(
            "🔔 Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling:",
            reply_markup=keyboard
        )
        return

    # Hudud tanlash
    if query.data.startswith("region_"):
        region = query.data.replace("region_", "")

        # Ma'lumotlar bazasiga saqlash
        conn = sqlite3.connect('bot_data.db')
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO users VALUES (?, ?, ?)",
                  (user_id, region, datetime.now().isoformat()))
        conn.commit()
        conn.close()

        # Asosiy menyu
        keyboard = [
            [InlineKeyboardButton("🕋 Namoz vaqtlari", callback_data="prayer_times")],
            [InlineKeyboardButton("📖 Qur'on tinglash", callback_data="quran_main")],
            [InlineKeyboardButton("🤲 Duolar", callback_data="duolar")],
            [InlineKeyboardButton("🌙 Ramazon", callback_data="ramadan_menu")],
            [InlineKeyboardButton("⚙️ Hududni o'zgartirish", callback_data="change_region")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            f"✅ Hudud tanlandi: {REGIONS[region]}\n\n"
            "Quyidagi bo'limlardan birini tanlang:",
            reply_markup=reply_markup
        )

    # Hududni o'zgartirish
    elif query.data == "change_region":
        keyboard = []
        row = []
        for key, value in REGIONS.items():
            row.append(InlineKeyboardButton(value, callback_data=f"region_{key}"))
            if len(row) == 2:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "🕌 Hududingizni tanlang:",
            reply_markup=reply_markup
        )

    # Namoz vaqtlari
    elif query.data == "prayer_times":
        conn = sqlite3.connect('bot_data.db')
        c = conn.cursor()
        c.execute("SELECT region FROM users WHERE user_id = ?", (user_id,))
        result = c.fetchone()
        conn.close()

        if result:
            region = result[0]

            # Aladhan API dan namoz vaqtlarini olish
            try:
                # Shahar koordinatalari (taxminiy)
                coordinates = {
                    "tashkent": {"lat": 41.2995, "lon": 69.2401},
                    "samarkand": {"lat": 39.6542, "lon": 66.9597},
                    "bukhara": {"lat": 39.7747, "lon": 64.4286},
                    "andijan": {"lat": 40.7821, "lon": 72.3442},
                    "fergana": {"lat": 40.3842, "lon": 71.7843},
                    "namangan": {"lat": 40.9983, "lon": 71.6726},
                    "kashkadarya": {"lat": 38.8361, "lon": 65.7892},
                    "surkhandarya": {"lat": 37.9406, "lon": 67.5719},
                    "jizzakh": {"lat": 40.1158, "lon": 67.8422},
                    "syrdarya": {"lat": 40.3833, "lon": 68.7167},
                    "navoi": {"lat": 40.0844, "lon": 65.3792},
                    "khorezm": {"lat": 41.3775, "lon": 60.3639},
                    "karakalpakstan": {"lat": 42.4611, "lon": 59.6103}
                }

                coord = coordinates.get(region, {"lat": 41.2995, "lon": 69.2401})

                # API so'rov
                today = datetime.now()
                url = f"http://api.aladhan.com/v1/timings/{today.strftime('%d-%m-%Y')}"
                params = {
                    "latitude": coord["lat"],
                    "longitude": coord["lon"],
                    "method": 2  # ISNA method
                }

                response = requests.get(url, params=params, timeout=5)
                data = response.json()

                if data.get("code") == 200:
                    timings = data["data"]["timings"]

                    text = f"🕌 {REGIONS[region]} - Namoz vaqtlari\n"
                    text += f"📅 {today.strftime('%d.%m.%Y')}\n\n"
                    text += f"🌅 Bomdod: {timings['Fajr']}\n"
                    text += f"🌄 Quyosh: {timings['Sunrise']}\n"
                    text += f"☀️ Peshin: {timings['Dhuhr']}\n"
                    text += f"🌤 Asr: {timings['Asr']}\n"
                    text += f"🌆 Shom: {timings['Maghrib']}\n"
                    text += f"🌙 Xufton: {timings['Isha']}\n"
                else:
                    text = f"🕌 {REGIONS[region]} - Namoz vaqtlari\n\n"
                    text += "❌ Vaqtlarni olishda xatolik yuz berdi"

            except Exception as e:
                text = f"🕌 {REGIONS[region]} - Namoz vaqtlari\n\n"
                text += "❌ Internet bilan bog'lanishda xatolik"

            keyboard = [[InlineKeyboardButton("🔙 Orqaga", callback_data="back_to_menu")]]
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

    # Qur'on asosiy menyu
    elif query.data == "quran_main":
        keyboard = []
        for i in range(1, 115, 10):
            end = min(i + 9, 114)
            keyboard.append([InlineKeyboardButton(
                f"{i} - {end} suralar",
                callback_data=f"quran_range_{i}_{end}"
            )])
        keyboard.append([InlineKeyboardButton("🔙 Orqaga", callback_data="back_to_menu")])

        await query.edit_message_text(
            "📖 Qur'oni Karim\n\nTinglashni xohlagan sura oralig'ini tanlang:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # Qur'on sura oralig'i
    elif query.data.startswith("quran_range_"):
        parts = query.data.split("_")
        start = int(parts[2])
        end = int(parts[3])

        keyboard = []
        for i in range(start, end + 1):
            keyboard.append([InlineKeyboardButton(
                f"{i}. {SURAHS[i]}",
                callback_data=f"surah_{i}"
            )])
        keyboard.append([InlineKeyboardButton("🔙 Orqaga", callback_data="quran_main")])

        await query.edit_message_text(
            "Surani tanlang:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # Sura yuklash
    elif query.data.startswith("surah_"):
        surah_num = int(query.data.split("_")[1])
        await query.edit_message_text(f"📥 {SURAHS[surah_num]} surasi yuklanmoqda...")

        # Mishari Rashid audio URL (formatlangan)
        audio_url = f"https://server8.mp3quran.net/afs/{str(surah_num).zfill(3)}.mp3"

        # Orqaga tugmasi uchun oraliqni aniqlash
        start_range = ((surah_num - 1) // 10) * 10 + 1
        end_range = min(start_range + 9, 114)

        try:
            await context.bot.send_audio(
                chat_id=query.message.chat_id,
                audio=audio_url,
                title=f"{surah_num}. {SURAHS[surah_num]}",
                performer="Mishari Rashid Al-Afasy"
            )

            # Orqaga tugmasi
            keyboard = [[InlineKeyboardButton("🔙 Orqaga", callback_data=f"quran_range_{start_range}_{end_range}")]]
            await query.edit_message_text(
                f"✅ {SURAHS[surah_num]} surasi yuklandi",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception as e:
            keyboard = [[InlineKeyboardButton("🔙 Orqaga", callback_data=f"quran_range_{start_range}_{end_range}")]]
            await query.edit_message_text(
                f"❌ Xatolik yuz berdi. Iltimos qaytadan urinib ko'ring.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

    # Duolar
    elif query.data == "duolar":
        conn = sqlite3.connect('bot_data.db')
        c = conn.cursor()
        c.execute("SELECT id, title FROM duolar")
        duas = c.fetchall()
        conn.close()

        if duas:
            keyboard = []
            for dua in duas:
                keyboard.append([InlineKeyboardButton(dua[1], callback_data=f"dua_{dua[0]}")])
            keyboard.append([InlineKeyboardButton("🔙 Orqaga", callback_data="back_to_menu")])

            await query.edit_message_text(
                "🤲 Duolar to'plami\n\nDuoni tanlang:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            keyboard = [[InlineKeyboardButton("🔙 Orqaga", callback_data="back_to_menu")]]
            await query.edit_message_text(
                "🤲 Hozircha duolar qo'shilmagan.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

    # Dua ko'rish
    elif query.data.startswith("dua_"):
        dua_id = int(query.data.split("_")[1])
        conn = sqlite3.connect('bot_data.db')
        c = conn.cursor()
        c.execute("SELECT title, content FROM duolar WHERE id = ?", (dua_id,))
        dua = c.fetchone()
        conn.close()

        if dua:
            keyboard = [[InlineKeyboardButton("🔙 Orqaga", callback_data="duolar")]]
            await query.edit_message_text(
                f"🤲 {dua[0]}\n\n{dua[1]}",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

    # Orqaga qaytish
    elif query.data == "back_to_menu":
        keyboard = [
            [InlineKeyboardButton("🕋 Namoz vaqtlari", callback_data="prayer_times")],
            [InlineKeyboardButton("📖 Qur'on tinglash", callback_data="quran_main")],
            [InlineKeyboardButton("🤲 Duolar", callback_data="duolar")],
            [InlineKeyboardButton("🌙 Ramazon", callback_data="ramadan_menu")],
            [InlineKeyboardButton("⚙️ Hududni o'zgartirish", callback_data="change_region")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            "Quyidagi bo'limlardan birini tanlang:",
            reply_markup=reply_markup
        )

    # Ramazon menyu
    elif query.data == "ramadan_menu":
        keyboard = [
            [InlineKeyboardButton("🌙 Ro'za vaqtlari", callback_data="ramadan_fasting")],
            [InlineKeyboardButton("📿 Ramazon duolari", callback_data="ramadan_duas")],
            [InlineKeyboardButton("📊 Ramazon kalkulyatori", callback_data="ramadan_calc")],
            [InlineKeyboardButton("💡 Ramazon tavsiyalari", callback_data="ramadan_tips")],
            [InlineKeyboardButton("🔙 Orqaga", callback_data="back_to_menu")]
        ]

        await query.edit_message_text(
            "🌙 Ramazon muborak!\n\n"
            "Quyidagi bo'limlardan birini tanlang:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # Ro'za vaqtlari
    elif query.data == "ramadan_fasting":
        conn = sqlite3.connect('bot_data.db')
        c = conn.cursor()
        c.execute("SELECT region FROM users WHERE user_id = ?", (user_id,))
        result = c.fetchone()
        conn.close()

        if result:
            region = result[0]

            try:
                coordinates = {
                    "tashkent": {"lat": 41.2995, "lon": 69.2401},
                    "samarkand": {"lat": 39.6542, "lon": 66.9597},
                    "bukhara": {"lat": 39.7747, "lon": 64.4286},
                    "andijan": {"lat": 40.7821, "lon": 72.3442},
                    "fergana": {"lat": 40.3842, "lon": 71.7843},
                    "namangan": {"lat": 40.9983, "lon": 71.6726},
                    "kashkadarya": {"lat": 38.8361, "lon": 65.7892},
                    "surkhandarya": {"lat": 37.9406, "lon": 67.5719},
                    "jizzakh": {"lat": 40.1158, "lon": 67.8422},
                    "syrdarya": {"lat": 40.3833, "lon": 68.7167},
                    "navoi": {"lat": 40.0844, "lon": 65.3792},
                    "khorezm": {"lat": 41.3775, "lon": 60.3639},
                    "karakalpakstan": {"lat": 42.4611, "lon": 59.6103}
                }

                coord = coordinates.get(region, {"lat": 41.2995, "lon": 69.2401})
                today = datetime.now()

                url = f"http://api.aladhan.com/v1/timings/{today.strftime('%d-%m-%Y')}"
                params = {
                    "latitude": coord["lat"],
                    "longitude": coord["lon"],
                    "method": 2
                }

                response = requests.get(url, params=params, timeout=5)
                data = response.json()

                if data.get("code") == 200:
                    timings = data["data"]["timings"]

                    text = f"🌙 {REGIONS[region]} - Ro'za vaqtlari\n"
                    text += f"📅 {today.strftime('%d.%m.%Y')}\n\n"
                    text += f"🍽 Saharlik: {timings['Fajr']} gacha\n"
                    text += f"🌅 Bomdod: {timings['Fajr']}\n"
                    text += f"🌆 Og'iz ochish: {timings['Maghrib']}\n"
                    text += f"🌙 Taroveh: {timings['Isha']} dan keyin\n"
                else:
                    text = "❌ Vaqtlarni olishda xatolik"

            except:
                text = "❌ Internet bilan bog'lanishda xatolik"

            keyboard = [[InlineKeyboardButton("🔙 Orqaga", callback_data="ramadan_menu")]]
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

    # Ramazon duolari
    elif query.data == "ramadan_duas":
        text = "📿 Ramazon duolari\n\n"
        text += "1️⃣ Saharlik duosi:\n"
        text += "نَوَيْتُ أَنْ أَصُومَ صَوْمَ شَهْرِ رَمَضَانَ\n"
        text += "Navaytu an asuvma savma shahri Ramazon\n\n"
        text += "2️⃣ Og'iz ochish duosi:\n"
        text += "اَللَّهُمَّ لَكَ صُمْتُ وَبِكَ آمَنْتُ وَعَلَيْكَ تَوَكَّلْتُ وَعَلَى رِزْقِكَ أَفْطَرْتُ\n"
        text += "Allohumma laka sumtu va bika aamantu va alayka tavakkaltu va ala rizqika aftartu\n\n"
        text += "3️⃣ Laylatul Qadr duosi:\n"
        text += "اَللَّهُمَّ إِنَّكَ عَفُوٌّ تُحِبُّ الْعَفْوَ فَاعْفُ عَنِّي\n"
        text += "Allohumma innaka afuvvun tuhibbul afva fa'fu anni"

        keyboard = [[InlineKeyboardButton("🔙 Orqaga", callback_data="ramadan_menu")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

    # Ramazon kalkulyatori
    elif query.data == "ramadan_calc":
        text = "📊 Ramazon kalkulyatori\n\n"
        text += "💰 Zakoti fitr: 45,000 so'm (2026)\n\n"
        text += "📝 Zakot hisoblash:\n"
        text += "• Oila a'zosi uchun 1 zakot to'lanadi\n"
        text += "• 85 gramm oltin qiymatidan ortiq boylik bo'lsa, 2.5% zakot beriladi\n\n"
        text += "🎁 Fidya (keksa, bemor):\n"
        text += "• Bir kun uchun: 45,000 so'm\n"
        text += "• Ramazon uchun (30 kun): 1,350,000 so'm\n\n"
        text += "💝 Sadaqa:\n"
        text += "• Ixtiyoriy miqdorda"

        keyboard = [[InlineKeyboardButton("🔙 Orqaga", callback_data="ramadan_menu")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

    # Ramazon tavsiyalari
    elif query.data == "ramadan_tips":
        text = "💡 Ramazon tavsiyalari\n\n"
        text += "✅ Ro'zaning fazilatlari:\n"
        text += "• Barcha gunohlar kechiriladi\n"
        text += "• Jahannam eshiklari yopiladi\n"
        text += "• Jannat eshiklari ochiladi\n"
        text += "• Shayton zanjirlanadi\n\n"
        text += "📖 Qur'on o'qish:\n"
        text += "• Har kuni kamida 1 juz o'qing\n"
        text += "• Taroveh namozida tinglang\n\n"
        text += "🤲 Ko'p duo qiling:\n"
        text += "• Og'iz ochishdan oldin\n"
        text += "• Tahajjud vaqtida\n"
        text += "• Laylatul Qadrda\n\n"
        text += "💝 Sadaqa bering:\n"
        text += "• Muhtojlarga yordam\n"
        text += "• Yaqinlaringizga ehson\n\n"
        text += "🌟 Oxirgi 10 kun:\n"
        text += "• E'tikofga o'tiring\n"
        text += "• Laylatul Qadrni qidiring\n"
        text += "• Ko'proq ibodatda bo'ling"

        keyboard = [[InlineKeyboardButton("🔙 Orqaga", callback_data="ramadan_menu")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# Admin panel
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Sizda admin huquqi yo'q!")
        return

    keyboard = [
        [InlineKeyboardButton("📢 Kanal qo'shish", callback_data="admin_add_channel")],
        [InlineKeyboardButton("🗑 Kanal o'chirish", callback_data="admin_del_channel")],
        [InlineKeyboardButton("📋 Kanallar ro'yxati", callback_data="admin_list_channels")],
        [InlineKeyboardButton("🤲 Dua qo'shish", callback_data="admin_add_dua")],
        [InlineKeyboardButton("📨 Xabar yuborish", callback_data="admin_send_message")],
        [InlineKeyboardButton("📊 Statistika", callback_data="admin_stats")]
    ]

    await update.message.reply_text(
        f"👨‍💼 Admin Panel {BOT_VERSION}\n\nKerakli bo'limni tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# Admin callback
async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    if query.from_user.id not in ADMIN_IDS:
        await query.answer("❌ Sizda admin huquqi yo'q!", show_alert=True)
        return

    await query.answer()

    if query.data == "admin_stats":
        conn = sqlite3.connect('bot_data.db')
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM users")
        user_count = c.fetchone()[0]
        conn.close()

        keyboard = [[InlineKeyboardButton("🔙 Orqaga", callback_data="admin_back")]]
        await query.edit_message_text(
            f"📊 Statistika\n\n"
            f"👥 Foydalanuvchilar: {user_count}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == "admin_add_channel":
        context.user_data['waiting_for'] = 'channel'
        keyboard = [[InlineKeyboardButton("❌ Bekor qilish", callback_data="admin_back")]]
        await query.edit_message_text(
            "📢 Kanal qo'shish\n\n"
            "Quyidagi formatda yuboring:\n\n"
            "@kanal_username\n"
            "Kanal nomi\n\n"
            "Misol:\n"
            "@islomiybot\n"
            "Islomiy Bilimlar",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == "admin_list_channels":
        conn = sqlite3.connect('bot_data.db')
        c = conn.cursor()
        c.execute("SELECT channel_id, channel_name FROM channels")
        channels = c.fetchall()
        conn.close()

        if channels:
            text = "📋 Kanallar ro'yxati:\n\n"
            for ch in channels:
                text += f"• {ch[1]}: {ch[0]}\n"
        else:
            text = "📋 Hozircha kanallar yo'q"

        keyboard = [[InlineKeyboardButton("🔙 Orqaga", callback_data="admin_back")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "admin_add_dua":
        context.user_data['waiting_for'] = 'dua'
        keyboard = [[InlineKeyboardButton("❌ Bekor qilish", callback_data="admin_back")]]
        await query.edit_message_text(
            "🤲 Dua qo'shish\n\n"
            "Quyidagi formatda yuboring:\n\n"
            "Dua sarlavhasi\n"
            "Dua matni\n\n"
            "Misol:\n"
            "Uxlashdan oldin o'qiladigan duo\n"
            "Bismika Allohumma amuutu wa ahya",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == "admin_send_message":
        context.user_data['waiting_for'] = 'broadcast'
        keyboard = [[InlineKeyboardButton("❌ Bekor qilish", callback_data="admin_back")]]
        await query.edit_message_text(
            "📨 Xabar yuborish\n\n"
            "Barcha foydalanuvchilarga yuboriladigan xabarni yozing.\n\n"
            "Xabar matn, rasm yoki video bo'lishi mumkin.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == "admin_back":
        if 'waiting_for' in context.user_data:
            del context.user_data['waiting_for']

        keyboard = [
            [InlineKeyboardButton("📢 Kanal qo'shish", callback_data="admin_add_channel")],
            [InlineKeyboardButton("🗑 Kanal o'chirish", callback_data="admin_del_channel")],
            [InlineKeyboardButton("📋 Kanallar ro'yxati", callback_data="admin_list_channels")],
            [InlineKeyboardButton("🤲 Dua qo'shish", callback_data="admin_add_dua")],
            [InlineKeyboardButton("📨 Xabar yuborish", callback_data="admin_send_message")],
            [InlineKeyboardButton("📊 Statistika", callback_data="admin_stats")]
        ]

        await query.edit_message_text(
            f"👨‍💼 Admin Panel {BOT_VERSION}\n\nKerakli bo'limni tanlang:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# Xabar yuborish handler (admin uchun)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Admin panel tugmasi
    if user_id in ADMIN_IDS and update.message.text == "👨‍💼 Admin Panel":
        keyboard = [
            [InlineKeyboardButton("📢 Kanal qo'shish", callback_data="admin_add_channel")],
            [InlineKeyboardButton("🗑 Kanal o'chirish", callback_data="admin_del_channel")],
            [InlineKeyboardButton("📋 Kanallar ro'yxati", callback_data="admin_list_channels")],
            [InlineKeyboardButton("🤲 Dua qo'shish", callback_data="admin_add_dua")],
            [InlineKeyboardButton("📨 Xabar yuborish", callback_data="admin_send_message")],
            [InlineKeyboardButton("📊 Statistika", callback_data="admin_stats")]
        ]

        await update.message.reply_text(
            f"👨‍💼 Admin Panel {BOT_VERSION}\n\nKerakli bo'limni tanlang:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    if user_id in ADMIN_IDS and 'waiting_for' in context.user_data:
        if context.user_data['waiting_for'] == 'channel':
            # Kanal qo'shish
            text = update.message.text
            parts = text.split('\n')
            if len(parts) == 2:
                channel_id = parts[0].strip()
                channel_name = parts[1].strip()

                conn = sqlite3.connect('bot_data.db')
                c = conn.cursor()
                c.execute("INSERT OR REPLACE INTO channels VALUES (?, ?)", (channel_id, channel_name))
                conn.commit()
                conn.close()

                await update.message.reply_text(f"✅ Kanal qo'shildi!\n\n{channel_name}\n{channel_id}")
                del context.user_data['waiting_for']
            else:
                await update.message.reply_text("❌ Noto'g'ri format! Pastdagi tugmadan qayta urinib ko'ring.")

        elif context.user_data['waiting_for'] == 'dua':
            # Dua qo'shish
            text = update.message.text
            parts = text.split('\n', 1)
            if len(parts) == 2:
                title = parts[0].strip()
                content = parts[1].strip()

                conn = sqlite3.connect('bot_data.db')
                c = conn.cursor()
                c.execute("INSERT INTO duolar (title, content) VALUES (?, ?)", (title, content))
                conn.commit()
                conn.close()

                await update.message.reply_text(f"✅ Dua qo'shildi!\n\n{title}")
                del context.user_data['waiting_for']
            else:
                await update.message.reply_text("❌ Noto'g'ri format! Pastdagi tugmadan qayta urinib ko'ring.")

        elif context.user_data['waiting_for'] == 'broadcast':
            # Barcha foydalanuvchilarga xabar yuborish
            conn = sqlite3.connect('bot_data.db')
            c = conn.cursor()
            c.execute("SELECT user_id FROM users")
            users = c.fetchall()
            conn.close()

            success = 0
            failed = 0

            status_msg = await update.message.reply_text(
                f"📨 Xabar yuborilmoqda...\n\n"
                f"✅ Yuborildi: {success}\n"
                f"❌ Xatolik: {failed}\n"
                f"📊 Jami: {len(users)}"
            )

            for user in users:
                try:
                    if update.message.text:
                        await context.bot.send_message(
                            chat_id=user[0],
                            text=update.message.text
                        )
                    elif update.message.photo:
                        await context.bot.send_photo(
                            chat_id=user[0],
                            photo=update.message.photo[-1].file_id,
                            caption=update.message.caption
                        )
                    elif update.message.video:
                        await context.bot.send_video(
                            chat_id=user[0],
                            video=update.message.video.file_id,
                            caption=update.message.caption
                        )
                    success += 1
                except Exception as e:
                    failed += 1

                # Har 10 ta foydalanuvchidan keyin statusni yangilash
                if (success + failed) % 10 == 0:
                    await status_msg.edit_text(
                        f"📨 Xabar yuborilmoqda...\n\n"
                        f"✅ Yuborildi: {success}\n"
                        f"❌ Xatolik: {failed}\n"
                        f"📊 Jami: {len(users)}"
                    )

            await status_msg.edit_text(
                f"✅ Xabar yuborish yakunlandi!\n\n"
                f"✅ Yuborildi: {success}\n"
                f"❌ Xatolik: {failed}\n"
                f"📊 Jami: {len(users)}"
            )
            del context.user_data['waiting_for']

# Main function
def main():
    init_db()

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("admin", admin))
    application.add_handler(CallbackQueryHandler(admin_callback, pattern="^admin_"))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO, handle_message))

    print("Bot ishga tushdi...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
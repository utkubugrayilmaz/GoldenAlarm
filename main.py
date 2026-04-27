"""
GoldenAlarm - Ana Bot Dosyası
Telegram bot ve zamanlayıcı burada çalışır.

Geliştirici: utku buğra yılmaz
GitHub: https://github.com/utkubugrayilmaz
"""

import os
import logging
from datetime import datetime

from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import TUM_URUNLER, CHECK_INTERVAL_MINUTES, ALTIN_TURLERI, OZEL_URUNLER
from services import gold_service, alarm_service

from aiohttp import web
import asyncio
# ============================================================
#                      YAPILANDIRMA
# ============================================================

# Environment variables yükle
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Logging ayarları
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
SELECTING_GOLD, ENTERING_PRICE, SELECTING_DIRECTION = range(3)


# ============================================================
#                    YARDIMCI FONKSİYONLAR
# ============================================================

def format_price(price: float) -> str:
    """Fiyatı formatla"""
    return f"{price:,.0f}".replace(",", ".")


async def send_notification(context: ContextTypes.DEFAULT_TYPE, text: str):
    """Bildirim gönder"""
    try:
        await context.bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=text,
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Bildirim gönderilemedi: {e}")


# ============================================================
#                    KOMUT HANDLERLARI
# ============================================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /start komutu
    Kullanıcıyı karşıla ve menüyü göster
    """
    welcome_text = """
🥇 <b>GoldenAlarm'a Hoş Geldin!</b>

Altın fiyatlarını takip et, alarm kur, fırsatları kaçırma.

<b>📋 Komutlar:</b>
/fiyat - Güncel altın fiyatları
/alarm - Yeni alarm kur
/alarmlar - Alarmlarını gör
/sil - Alarm sil
/yardim - Yardım

<b>⚙️ Sistem:</b>
• Fiyatlar 5 dakikada bir kontrol edilir
• Hedefe ulaşınca bildirim gelir
• Fiyat değişmeye devam ederse takip bildirimi alırsın

💡 Hemen /alarm yazarak başla!
"""
    await update.message.reply_text(welcome_text, parse_mode="HTML")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/yardim komutu"""
    help_text = """
📖 <b>Nasıl Kullanılır?</b>

<b>1️⃣ Fiyat Öğrenme:</b>
/fiyat yazınca tüm güncel fiyatları görürsün.

<b>2️⃣ Alarm Kurma:</b>
/alarm yaz → Altın seç → Hedef fiyat gir → Yön seç (↑ veya ↓)

<b>3️⃣ Alarm Yönetimi:</b>
/alarmlar - Tüm alarmları listele
/sil - Alarm sil

<b>📈 Yön Ne Demek?</b>
• <b>Yukarı (↑):</b> Fiyat X'e çıkınca haber ver
• <b>Aşağı (↓):</b> Fiyat X'e düşünce haber ver

<b>🔔 Takip Bildirimi:</b>
Alarm tetiklendikten sonra fiyat her 1.000₺ değişimde tekrar bildirim alırsın.
"""
    await update.message.reply_text(help_text, parse_mode="HTML")


async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /fiyat komutu
    Güncel altın fiyatlarını göster
    """
    await update.message.reply_text("🔄 Fiyatlar alınıyor...")

    result = gold_service.fetch_prices()

    if not result["success"]:
        await update.message.reply_text(f"❌ Hata: {result['error']}")
        return

    data = result["data"]
    update_time = gold_service.get_update_time(data)

    text = f"📊 <b>GÜNCEL ALTIN FİYATLARI</b>\n"
    text += f"🕐 <i>{update_time}</i>\n\n"

    # Altınlar
    text += "🪙 <b>Altınlar</b>\n"
    for kod, bilgi in ALTIN_TURLERI.items():
        fiyat = gold_service.get_price(kod, data)
        if fiyat:
            text += f"  {bilgi['emoji']} {bilgi['ad']}: <b>{format_price(fiyat)} ₺</b>\n"

    # Özel ürünler (Ajda)
    text += "\n📿 <b>Bilezikler</b>\n"
    for kod, bilgi in OZEL_URUNLER.items():
        fiyat = gold_service.get_price(kod, data)
        if fiyat:
            text += f"  {bilgi['emoji']} {bilgi['ad']}: <b>{format_price(fiyat)} ₺</b>\n"

    await update.message.reply_text(text, parse_mode="HTML")


# ============================================================
#                    ALARM OLUŞTURMA (Conversation)
# ============================================================

async def alarm_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /alarm komutu
    Alarm oluşturma sürecini başlat
    """
    # Inline keyboard oluştur - Altınlar
    keyboard = []

    # Ajda bileziği en üstte
    keyboard.append([
        InlineKeyboardButton("📿 10gr Ajda", callback_data="gold_AJDA_10GR"),
        InlineKeyboardButton("📿 5gr Ajda", callback_data="gold_AJDA_5GR"),
    ])
    keyboard.append([
        InlineKeyboardButton("📿 15gr Ajda", callback_data="gold_AJDA_15GR"),
        InlineKeyboardButton("📿 20gr Ajda", callback_data="gold_AJDA_20GR"),
    ])

    # Diğer altınlar
    keyboard.append([
        InlineKeyboardButton("🥇 Gram Altın", callback_data="gold_HAS"),
        InlineKeyboardButton("📿 22 Ayar", callback_data="gold_YIA"),
    ])
    keyboard.append([
        InlineKeyboardButton("🪙 Çeyrek", callback_data="gold_CEYREKALTIN"),
        InlineKeyboardButton("🪙 Yarım", callback_data="gold_YARIMALTIN"),
    ])
    keyboard.append([
        InlineKeyboardButton("🪙 Tam", callback_data="gold_TAMALTIN"),
        InlineKeyboardButton("🏅 Cumhuriyet", callback_data="gold_CUMHURIYETALTINI"),
    ])
    keyboard.append([
        InlineKeyboardButton("🏅 Ata", callback_data="gold_ATAALTIN"),
        InlineKeyboardButton("🏅 Reşat", callback_data="gold_RESATALTIN"),
    ])
    keyboard.append([
        InlineKeyboardButton("❌ İptal", callback_data="cancel"),
    ])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🪙 <b>Hangi altın için alarm kurmak istiyorsun?</b>",
        reply_markup=reply_markup,
        parse_mode="HTML"
    )

    return SELECTING_GOLD


async def gold_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Altın seçildiğinde"""
    query = update.callback_query
    await query.answer()

    if query.data == "cancel":
        await query.edit_message_text("❌ Alarm kurma iptal edildi.")
        return ConversationHandler.END

    # Seçilen altını kaydet
    gold_code = query.data.replace("gold_", "")
    context.user_data["alarm_gold"] = gold_code

    # Güncel fiyatı göster
    result = gold_service.fetch_prices()
    current_price = 0

    if result["success"]:
        current_price = gold_service.get_price(gold_code, result["data"])

    gold_name = TUM_URUNLER[gold_code]["ad"]

    text = f"📍 <b>{gold_name}</b> seçildi.\n\n"

    if current_price:
        text += f"💰 Güncel fiyat: <b>{format_price(current_price)} ₺</b>\n\n"

    text += "🎯 <b>Hedef fiyatı yaz:</b>\n"
    text += "<i>(Örnek: 62000 veya 62.000)</i>"

    await query.edit_message_text(text, parse_mode="HTML")

    return ENTERING_PRICE


async def price_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fiyat girildiğinde"""
    text = update.message.text.strip()

    # Fiyatı parse et
    try:
        # Nokta ve virgülleri temizle
        clean_price = text.replace(".", "").replace(",", "").replace(" ", "")
        target_price = float(clean_price)

        if target_price <= 0:
            raise ValueError("Fiyat pozitif olmalı")

    except ValueError:
        await update.message.reply_text(
            "❌ Geçersiz fiyat. Lütfen sadece sayı gir.\n"
            "<i>Örnek: 62000 veya 62.000</i>",
            parse_mode="HTML"
        )
        return ENTERING_PRICE

    context.user_data["alarm_price"] = target_price

    # Yön seçimi
    keyboard = [
        [
            InlineKeyboardButton("📈 Yukarı (fiyat yükselince)", callback_data="dir_yukari"),
        ],
        [
            InlineKeyboardButton("📉 Aşağı (fiyat düşünce)", callback_data="dir_asagi"),
        ],
        [
            InlineKeyboardButton("❌ İptal", callback_data="cancel"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    gold_code = context.user_data["alarm_gold"]
    gold_name = TUM_URUNLER[gold_code]["ad"]

    await update.message.reply_text(
        f"📍 {gold_name}\n"
        f"🎯 Hedef: <b>{format_price(target_price)} ₺</b>\n\n"
        f"📊 <b>Ne zaman haber vereyim?</b>",
        reply_markup=reply_markup,
        parse_mode="HTML"
    )

    return SELECTING_DIRECTION


async def direction_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Yön seçildiğinde - Alarm oluştur"""
    query = update.callback_query
    await query.answer()

    if query.data == "cancel":
        await query.edit_message_text("❌ Alarm kurma iptal edildi.")
        context.user_data.clear()
        return ConversationHandler.END

    direction = query.data.replace("dir_", "")
    gold_code = context.user_data["alarm_gold"]
    target_price = context.user_data["alarm_price"]

    # Alarmı kaydet
    alarm = alarm_service.add(gold_code, target_price, direction)

    if alarm:
        direction_text = "📈 Yukarı (yükselince)" if direction == "yukari" else "📉 Aşağı (düşünce)"

        text = f"""
✅ <b>ALARM KURULDU!</b>

{alarm['emoji']} <b>{alarm['urun_adi']}</b>
🎯 Hedef: <b>{format_price(target_price)} ₺</b>
📊 Yön: {direction_text}

🔔 Hedefe ulaşınca bildirim alacaksın.
📱 Sonrasında her 1.000₺ değişimde takip bildirimi gelecek.
"""
        await query.edit_message_text(text, parse_mode="HTML")
    else:
        await query.edit_message_text("❌ Alarm eklenirken bir hata oluştu.")

    context.user_data.clear()
    return ConversationHandler.END


async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Conversation'ı iptal et"""
    context.user_data.clear()

    if update.callback_query:
        await update.callback_query.edit_message_text("❌ İşlem iptal edildi.")
    else:
        await update.message.reply_text("❌ İşlem iptal edildi.")

    return ConversationHandler.END


# ============================================================
#                    ALARM YÖNETİMİ
# ============================================================

async def list_alarms_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/alarmlar komutu"""
    alarms = alarm_service.get_all()

    if not alarms:
        await update.message.reply_text(
            "📭 Henüz kurulu alarm yok.\n\n"
            "💡 /alarm yazarak yeni alarm kurabilirsin."
        )
        return

    text = "🔔 <b>ALARMLARIM</b>\n\n"

    for alarm in alarms:
        status = "✅" if alarm["aktif"] else "⏸️"
        triggered = "🔔" if alarm["tetiklendi"] else "⏳"
        direction = "📈" if alarm["yon"] == "yukari" else "📉"

        text += f"{status} <b>#{alarm['id']}</b> {alarm['emoji']} {alarm['urun_adi']}\n"
        text += f"    {direction} Hedef: <b>{format_price(alarm['hedef_fiyat'])} ₺</b>\n"
        text += f"    {triggered} {'Tetiklendi' if alarm['tetiklendi'] else 'Bekliyor'}\n\n"

    text += "💡 Silmek için /sil"

    await update.message.reply_text(text, parse_mode="HTML")


async def delete_alarm_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/sil komutu"""
    alarms = alarm_service.get_all()

    if not alarms:
        await update.message.reply_text("📭 Silinecek alarm yok.")
        return

    keyboard = []

    for alarm in alarms:
        direction = "↑" if alarm["yon"] == "yukari" else "↓"
        btn_text = f"#{alarm['id']} {alarm['emoji']} {alarm['urun_adi']} {direction} {format_price(alarm['hedef_fiyat'])}₺"
        keyboard.append([
            InlineKeyboardButton(btn_text, callback_data=f"delete_{alarm['id']}")
        ])

    keyboard.append([InlineKeyboardButton("❌ İptal", callback_data="delete_cancel")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🗑️ <b>Hangi alarmı silmek istiyorsun?</b>",
        reply_markup=reply_markup,
        parse_mode="HTML"
    )


async def delete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Alarm silme callback'i"""
    query = update.callback_query
    await query.answer()

    if query.data == "delete_cancel":
        await query.edit_message_text("❌ Silme iptal edildi.")
        return

    alarm_id = int(query.data.replace("delete_", ""))
    alarm = alarm_service.get_by_id(alarm_id)

    if alarm and alarm_service.delete(alarm_id):
        await query.edit_message_text(
            f"🗑️ <b>Alarm silindi!</b>\n\n"
            f"{alarm['emoji']} {alarm['urun_adi']}\n"
            f"🎯 Hedef: {format_price(alarm['hedef_fiyat'])} ₺",
            parse_mode="HTML"
        )
    else:
        await query.edit_message_text("❌ Alarm silinemedi.")


#test
async def test_alarm_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /test komutu
    Alarm sistemini mock veri ile test et
    """
    alarms = alarm_service.get_all()

    if not alarms:
        await update.message.reply_text(
            "⚠️ Test için önce bir alarm kur.\n"
            "/alarm yazarak alarm kurabilirsin."
        )
        return

    await update.message.reply_text("🧪 <b>TEST MODU</b>\n\nAlarmlar simüle ediliyor...", parse_mode="HTML")

    # Her alarm için sahte tetikleme bildirimi gönder
    for alarm in alarms:
        if not alarm["aktif"]:
            continue

        # Sahte fiyat (hedefin biraz üstünde/altında)
        if alarm["yon"] == "yukari":
            fake_price = alarm["hedef_fiyat"] + 500
            yon_emoji = "📈"
        else:
            fake_price = alarm["hedef_fiyat"] - 500
            yon_emoji = "📉"

        text = f"""
🧪 <b>TEST - ALARM TETİKLENDİ!</b>

{yon_emoji} {alarm['emoji']} <b>{alarm['urun_adi']}</b>

🎯 Hedef: {format_price(alarm['hedef_fiyat'])} ₺
💰 Test Fiyat: <b>{format_price(fake_price)} ₺</b>

⚠️ <i>Bu bir test bildirimidir.</i>
"""
        await update.message.reply_text(text, parse_mode="HTML")

    await update.message.reply_text("✅ Test tamamlandı!\n\n<i>Gerçek alarmlar fiyat değişimlerinde tetiklenecek.</i>",
                                    parse_mode="HTML")


# ============================================================
#                    ZAMANLI GÖREVLER
# ============================================================

async def check_prices_job(context: ContextTypes.DEFAULT_TYPE):
    """
    Her 5 dakikada bir çalışan fiyat kontrol görevi
    """
    logger.info("⏰ Fiyat kontrolü başladı...")

    result = gold_service.fetch_prices()

    if not result["success"]:
        logger.error(f"API hatası: {result['error']}")
        return

    data = result["data"]

    # Alarmları kontrol et
    notifications = alarm_service.check_alarms(gold_service, data)

    for notif in notifications:
        alarm = notif["alarm"]
        guncel_fiyat = notif["guncel_fiyat"]

        if notif["type"] == "trigger":
            # İlk tetikleme
            yon_emoji = "📈" if alarm["yon"] == "yukari" else "📉"

            text = f"""
🔔 <b>ALARM TETİKLENDİ!</b>

{yon_emoji} {alarm['emoji']} <b>{alarm['urun_adi']}</b>

🎯 Hedef: {format_price(alarm['hedef_fiyat'])} ₺
💰 Güncel: <b>{format_price(guncel_fiyat)} ₺</b>

⏰ {datetime.now().strftime("%d.%m.%Y %H:%M")}
"""
        else:
            # Takip bildirimi
            fark = notif["fark"]
            yon_emoji = "🚀" if alarm["yon"] == "yukari" else "📉"
            durum = "yükselmeye devam ediyor" if fark > 0 else "düşmeye devam ediyor"

            text = f"""
{yon_emoji} <b>TAKİP BİLDİRİMİ</b>

{alarm['emoji']} <b>{alarm['urun_adi']}</b> {durum}!

🎯 Hedefin: {format_price(alarm['hedef_fiyat'])} ₺
💰 Şu an: <b>{format_price(guncel_fiyat)} ₺</b>
📊 Değişim: {format_price(abs(fark))} ₺ {'artış' if fark > 0 else 'düşüş'}

⏰ {datetime.now().strftime("%d.%m.%Y %H:%M")}
"""

        await send_notification(context, text)
        logger.info(f"🔔 Bildirim gönderildi: {alarm['urun_adi']}")

    logger.info(f"✅ Fiyat kontrolü tamamlandı. {len(notifications)} bildirim gönderildi.")


# ============================================================
#                    ANA FONKSİYON
# ============================================================

# ============================================================
#                    WEB SERVER (Render için)
# ============================================================

async def health_handler(request):
    """Health check endpoint - UptimeRobot bunu pingleyecek"""
    return web.Response(text="OK")


async def run_webserver():
    """Basit web server çalıştır"""
    app = web.Application()
    app.router.add_get("/", health_handler)
    app.router.add_get("/health", health_handler)

    port = int(os.getenv("PORT", 8080))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"🌐 Web server başlatıldı (port {port})")


# ============================================================
#                    ANA FONKSİYON
# ============================================================

def main():
    """Botu başlat"""

    if not TELEGRAM_TOKEN:
        logger.error("❌ TELEGRAM_TOKEN bulunamadı!")
        return

    if not TELEGRAM_CHAT_ID:
        logger.error("❌ TELEGRAM_CHAT_ID bulunamadı!")
        return

    logger.info("🚀 GoldenAlarm başlatılıyor...")

    # Application oluştur
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # Alarm oluşturma conversation handler
    alarm_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("alarm", alarm_command)],
        states={
            SELECTING_GOLD: [CallbackQueryHandler(gold_selected)],
            ENTERING_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, price_entered)],
            SELECTING_DIRECTION: [CallbackQueryHandler(direction_selected)],
        },
        fallbacks=[
            CommandHandler("iptal", cancel_conversation),
            CallbackQueryHandler(cancel_conversation, pattern="^cancel$"),
        ],
    )

    # Handler'ları ekle
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("yardim", help_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("fiyat", price_command))
    app.add_handler(CommandHandler("alarmlar", list_alarms_command))
    app.add_handler(CommandHandler("sil", delete_alarm_command))
    app.add_handler(CommandHandler("test", test_alarm_command))
    app.add_handler(CallbackQueryHandler(delete_callback, pattern="^delete_"))
    app.add_handler(alarm_conv_handler)

    # Scheduler oluştur
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        check_prices_job,
        "interval",
        minutes=CHECK_INTERVAL_MINUTES,
        args=[app],
        id="price_check",
        replace_existing=True
    )

    # İlk kontrolü hemen yap
    async def startup(application):
        await check_prices_job(application)
        # Web server'ı başlat (Render için)
        await run_webserver()

    app.post_init = startup

    # Scheduler'ı başlat
    scheduler.start()
    logger.info(f"⏰ Zamanlayıcı başlatıldı ({CHECK_INTERVAL_MINUTES} dakika aralıkla)")

    # Botu çalıştır
    logger.info("✅ Bot çalışıyor!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()



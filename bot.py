import os
import logging
import httpx
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = "8922544964:AAHreUn_UkIamBmtvNi5uyaGpd6qvfEq3LY"

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"أهلاً بك {update.effective_user.first_name}! 👋\n\n"
        "أرسل لي أي رابط فيديو من (TikTok, Instagram, YouTube) وسأقوم بتحميله لك فوراً وبدون علامة مائية! 📥"
    )

async def download_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    
    if not (url.startswith("http://") or url.startswith("https://")):
        return

    status_msg = await update.message.reply_text("⏳ جاري التحميل لتجاوز الحظر...")

    try:
        # استخدام API سريع لتنزيل مقاطع TikTok بدون علامة مائية وتجاوز حظر الـ IP
        if "tiktok.com" in url:
            api_url = f"https://api.tiklydown.eu.org/api/download?url={url}"
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(api_url)
                data = response.json()
                
                # الحصول على رابط الفيديو المباشر
                video_url = data.get("video", {}).get("noWatermark") or data.get("video", {}).get("watermark")
                
                if video_url:
                    await status_msg.edit_text("⬆️ جاري إرسال الفيديو...")
                    await update.message.reply_video(video=video_url)
                    await status_msg.delete()
                    return

        await status_msg.edit_text("❌ تعذر تحميل هذا الفيديو، تأكد من صحة الرابط.")

    except Exception as e:
        logging.error(f"Error: {e}")
        await status_msg.edit_text("❌ حدث خطأ أثناء الاتصال بالسيرفر. أعد المحاولة برابط آخر.")

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_media))
    app.run_polling()

import os
import logging
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

BOT_TOKEN = "8922544964:AAHreUn_UkIamBmtvNi5uyaGpd6qvfEq3LY"

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"أهلاً بك {update.effective_user.first_name}! 👋\n\n"
        "أرسل لي أي رابط فيديو من (TikTok, Instagram, YouTube) وسأقوم بتحميله لك فوراً! 📥"
    )

async def download_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    
    if not (url.startswith("http://") or url.startswith("https://")):
        return

    status_msg = await update.message.reply_text("⏳ جاري معالجة التحميل...")

    # خيارات متقدمة لـ yt-dlp لمعالجة الروابط المختصرة وتجاوز القيود
    ydl_opts = {
        'format': 'best',
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'allow_unplayable_formats': False,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }

    try:
        loop = asyncio.get_event_loop()
        file_path = await loop.run_in_executor(None, lambda: _extract_and_download(url, ydl_opts))

        if file_path and os.path.exists(file_path):
            await status_msg.edit_text("⬆️ جاري إرسال الفيديو...")
            with open(file_path, 'rb') as video:
                await update.message.reply_video(video=video)
            
            # حذف الملف بعد الإرسال لتوفير المساحة
            os.remove(file_path)
            await status_msg.delete()
        else:
            await status_msg.edit_text("❌ تعذر تحميل هذا الفيديو. تأكد من صحة الرابط أو حاول لاحقاً.")

    except Exception as e:
        logging.error(f"Error downloading: {e}")
        await status_msg.edit_text("❌ حدث خطأ أثناء التحميل. أعد المحاولة برابط آخر.")

def _extract_and_download(url, opts):
    os.makedirs('downloads', exist_ok=True)
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        return filename

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_media))
    app.run_polling()

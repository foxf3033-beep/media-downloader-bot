import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

BOT_TOKEN = "8922544964:AAFVguH0mAk7ZT17nYQceSm3wXMw7NtVrI8"

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"أهلاً بك {update.effective_user.first_name}! 👋\n\n"
        "أرسل لي رابط أي فيديو من (TikTok, Instagram, YouTube) وسأقوم بتحميله لك فوراً بدون علامة مائية! 📥"
    )

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url.startswith("http"):
        return

    status_msg = await update.message.reply_text("⏳ جاري معالجة وتحميل الفيديو...")

    ydl_opts = {
        'format': 'best',
        'outtmpl': 'downloaded_video.mp4',
        'max_filesize': 50 * 1024 * 1024,
        'quiet': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        if os.path.exists("downloaded_video.mp4"):
            await status_msg.edit_text("⬆️ جاري إرسال الفيديو...")
            with open("downloaded_video.mp4", "rb") as video:
                await update.message.reply_video(video=video)
            
            os.remove("downloaded_video.mp4")
            await status_msg.delete()
        else:
            await status_msg.edit_text("❌ حدث خطأ أثناء جلب الفيديو.")

    except Exception as e:
        logging.error(f"Error: {e}")
        await status_msg.edit_text("❌ تعذر تحميل هذا الفيديو. تأكد من صحة الرابط أو الحجم.")
        if os.path.exists("downloaded_video.mp4"):
            os.remove("downloaded_video.mp4")

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))
    print("Bot is running...")
    app.run_polling()

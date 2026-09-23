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
        "أرسل لي أي رابط فيديو من TikTok وسأقوم بتحميله لك فوراً وبدون علامة مائية! 📥"
    )

async def download_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    
    if not (url.startswith("http://") or url.startswith("https://")):
        return

    status_msg = await update.message.reply_text("⏳ جاري استخراج الفيديو...")

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            # 1. تتبع الرابط المختصر للوصول للرابط المباشر
            resp = await client.get(url)
            final_url = str(resp.url)

            # 2. الاستعلام من API متلائم مع جميع صيغ تيك توك
            api_endpoint = f"https://api.tiklydown.eu.org/api/download?url={final_url}"
            api_resp = await client.get(api_endpoint)
            data = api_resp.json()

            # استخراج رابط الفيديو
            video_url = None
            if "video" in data:
                video_url = data["video"].get("noWatermark") or data["video"].get("watermark")
            elif "url" in data:
                video_url = data.get("url")

            if video_url:
                await status_msg.edit_text("⬆️ جاري إرسال الفيديو...")
                await update.message.reply_video(video=video_url)
                await status_msg.delete()
            else:
                await status_msg.edit_text("❌ تعذر استخراج رابط الفيديو. جرب رابطاً آخر.")

    except Exception as e:
        logging.error(f"Error handling request: {e}")
        await status_msg.edit_text("❌ تعذر تحميل هذا الفيديو حالياً. تأكد من صحة الرابط أو حاول لاحقاً.")

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_media))
    app.run_polling()

import logging
import httpx
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# إعداد السجلات لمتابعة أي أخطاء
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

BOT_TOKEN = "8922544964:AAHreUn_UkIamBmtvNi5uyaGpd6qvfEq3LY"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"أهلاً بك {update.effective_user.first_name}! 👋\n\n"
        "أرسل لي أي رابط فيديو من TikTok وسأقوم بتحميله لك فوراً وبدون علامة مائية! 🎂"
    )

async def download_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    if not ("tiktok.com" in url or "vt.tiktok.com" in url):
        return

    status_msg = await update.message.reply_text("⏳ جاري استخراج الفيديو...")

    try:
        async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
            # استخدام API TikWM المباشر والسريع
            api_url = "https://www.tikwm.com/api/"
            response = await client.post(api_url, data={"url": url})
            res_data = response.json()

            if res_data.get("code") == 0 and "data" in res_data:
                video_data = res_data["data"]
                # جلب رابط الفيديو بدون علامة مائية
                play_url = video_data.get("play") or video_data.get("wmplay")
                
                if play_url:
                    # إضافة النطاق إذا كان الرابط نسبياً
                    if play_url.startswith("/"):
                        play_url = f"https://www.tikwm.com{play_url}"
                        
                    await status_msg.edit_text("⬆️ جاري إرسال الفيديو...")
                    await update.message.reply_video(video=play_url)
                    await status_msg.delete()
                    return

            await status_msg.edit_text("❌ تعذر استخراج رابط الفيديو. تأكد من صحة الرابط وجرب مرة أخرى.")

    except Exception as e:
        logging.error(f"Error handling request: {e}")
        await status_msg.edit_text("❌ حدث خطأ أثناء التحميل. تأكد من صحة الرابط أو حاول لاحقاً.")

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_media))
    app.run_polling()

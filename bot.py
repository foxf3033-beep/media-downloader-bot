import logging
import httpx
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.error import TelegramError

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

BOT_TOKEN = "8922544964:AAHreUn_UkIamBmtvNi5uyaGpd6qvfEq3LY"

# معرف القناة الأولى الخاصة بك
CHANNEL_1 = "@my_tiktok_channel_4"
# إذا كان لديك قناة ثانية استبدل المعرف هنا، أو يمكنك ترك نفس القناة مؤقتاً
CHANNEL_2 = "@my_tiktok_channel_4"

async def is_user_subscribed(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """التحقق من اشتراك المستخدم في القنوات"""
    channels = list(set([CHANNEL_1, CHANNEL_2]))  # لإزالة التكرار إن وجد
    for ch in channels:
        try:
            member = await context.bot.get_chat_member(chat_id=ch, user_id=user_id)
            if member.status in ['left', 'kicked']:
                return False
        except TelegramError as e:
            logging.error(f"Failed to check membership for channel {ch}: {e}")
            return False
    return True

def get_subscribe_keyboard() -> InlineKeyboardMarkup:
    """إنشاء أزرار القنوات مع زر التحقق"""
    keyboard = [
        [InlineKeyboardButton("📢 قناة البوت الرسمية", url=f"https://t.me/{CHANNEL_1.replace('@', '')}")],
        [InlineKeyboardButton("✅ اشتركت، تحقق الآن", callback_data="check_sub")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_user_subscribed(user_id, context):
        await update.message.reply_text(
            "⚠️ لاستخدام البوت، يجب عليك الاشتراك في قناة البوت أولاً:",
            reply_markup=get_subscribe_keyboard()
        )
        return

    await update.message.reply_text(
        f"أهلاً بك {update.effective_user.first_name}! 👋\n\n"
        "أرسل لي أي رابط فيديو من TikTok وسأقوم بتحميله لك فوراً وبدون علامة مائية!"
    )

async def check_subscription_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الضغط على زر التحقق من الاشتراك"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    if await is_user_subscribed(user_id, context):
        await query.edit_message_text(
            "✅ تم التحقق من الاشتراك بنجاح!\n\n"
            "أرسل لي الآن أي رابط فيديو من TikTok لتحميله."
        )
    else:
        await query.answer("❌ لم تشترك في القناة بعد! يرجى الاشتراك ثم الضغط على الزر مرة أخرى.", show_alert=True)

async def download_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # فحص الاشتراك قبل المعالجة
    if not await is_user_subscribed(user_id, context):
        await update.message.reply_text(
            "⚠️ عذراً، يجب عليك الاشتراك في القناة أولاً لاستخدام البوت:",
            reply_markup=get_subscribe_keyboard()
        )
        return

    url = update.message.text.strip()
    if "tiktok.com" not in url:
        return

    status_msg = await update.message.reply_text("⏳ جاري استخراج الفيديو...")

    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36"
    }

    try:
        async with httpx.AsyncClient(timeout=30.0, verify=False, follow_redirects=True, headers=headers) as client:
            api_endpoint = "https://www.tikwm.com/api/"
            response = await client.post(api_endpoint, data={"url": url})
            res_data = response.json()

            if res_data.get("code") == 0 and "data" in res_data:
                video_data = res_data["data"]
                play_url = video_data.get("play") or video_data.get("wmplay")
                
                if play_url:
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
    app.add_handler(CallbackQueryHandler(check_subscription_button, pattern="^check_sub$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_media))
    
    app.run_polling()

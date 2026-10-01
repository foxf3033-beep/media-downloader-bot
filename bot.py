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

# معرف القناة الخاصة بك للاشتراك الإجباري
CHANNEL_1 = "@my_tiktok_channel_4"
CHANNEL_2 = "@my_tiktok_channel_4"

# رابط الإعلانات المباشر الخاص بك (Direct Link من Adsterra)
AD_LINK = "https://your-ad-link-here.com"

async def is_user_subscribed(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """التحقق من اشتراك المستخدم في القنوات"""
    channels = list(set([CHANNEL_1, CHANNEL_2]))
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
        "أرسل لي أي رابط فيديو من TikTok وسأقوم بتحميله لك فوراً وبدون علامة مائية!\n\n"
        "💻 **المطور:** wd wil"
    )

async def check_subscription_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الضغط على زر التحقق من الاشتراك"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    if await is_user_subscribed(user_id, context):
        await query.edit_message_text(
            "✅ تم التحقق من الاشتراك بنجاح!\n\n"
            "أرسل لي الآن أي رابط فيديو من TikTok لتحميله.\n\n"
            "💻 **المطور:** wd wil"
        )
    else:
        await query.answer("❌ لم تشترك في القناة بعد! يرجى الاشتراك ثم الضغط على الزر مرة أخرى.", show_alert=True)

async def download_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # فحص الاشتراك الإجباري أولاً
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
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }

    try:
        async with httpx.AsyncClient(timeout=30.0, verify=False, follow_redirects=True, headers=headers) as client:
            # معالجة الروابط المختصرة وتتبع إعادة التوجيه
            if "vt.tiktok.com" in url or "vm.tiktok.com" in url:
                resp = await client.get(url)
                url = str(resp.url)

            api_endpoint = "https://www.tikwm.com/api/"
            response = await client.post(api_endpoint, data={"url": url})
            res_data = response.json()

            if res_data.get("code") == 0 and "data" in res_data:
                video_data = res_data["data"]
                play_url = video_data.get("play") or video_data.get("wmplay")
                
                if play_url:
                    if play_url.startswith("/"):
                        play_url = f"https://www.tikwm.com{play_url}"
                        
                    await status_msg.delete()
                    
                    # زر إعلاني تحت الفيديو لتحقيق الأرباح
                    keyboard = [
                        [InlineKeyboardButton("🔗 اضغط هنا لدعم البوت وتوليد رابط إضافي", url=AD_LINK)]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)

                    await update.message.reply_video(
                        video=play_url, 
                        caption="✅ تم تحميل الفيديو بنجاح بدون علامة مائية!\n💡 لدعم استمرار البوت مجاناً، نرجو النقر على الزر أدناه:",
                        reply_markup=reply_markup
                    )
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

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

# رابط الإعلانات المباشر الخاص بك
AD_LINK = "https://www.profitableratecpmnetwork.com/kc0ukqgr?key=265d6e72d7a3c187616e16bce28bf1aa"

# مخزن مؤقت لحفظ روابط تيك توك للمستخدمين مؤقتاً لحين الضغط على الأزرار
USER_URLS = {}

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
    """إنشاء أزرار القنوات مع زر التحقق من الاشتراك"""
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
        "أرسل لي أي رابط فيديو من TikTok وسأقوم بتحجهيزه لك فوراً!\n\n"
        "💻 **المطور:** wd wil"
    )

async def check_subscription_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

async def handle_tiktok_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    # حفظ الرابط مؤقتاً لهذا المستخدم
    USER_URLS[user_id] = url

    # إرسال رسالة الخطوة الأولى الجديدة فقط (مع إلغاء القديمة تماماً)
    keyboard = [
        [InlineKeyboardButton("🔗 اضغط هنا لفتح رابط الدعم والإعلان أولاً", url=AD_LINK)],
        [InlineKeyboardButton("✅ لقد شاهدت الإعلان، اضغط هنا للمتابعة", callback_data="show_download_btn")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "📌 **الخطوة الأولى:**\n\n"
        "لتحميل الفيديو بدون علامة مائية، يرجى النقر على **رابط الدعم** أعلاه أولاً لتصفح الإعلان، ثم اضغط على زر التأكيد أدناه:",
        reply_markup=reply_markup
    )

async def show_download_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if user_id not in USER_URLS:
        await query.answer("⚠️ انتهت صلاحية الجلسة، يرجى إرسال الرابط من جديد.", show_alert=True)
        return

    # تحديث نفس الرسالة لتصبح خاصة بزر التحميل النهائي فقط
    keyboard = [
        [InlineKeyboardButton("📥 اضغط هنا لتحميل الفيديو بدون علامة مائية", callback_data="get_final_video")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.edit_text(
        "🎉 **ممتاز! تم التحقق من تفاعلك.**\n\n"
        "الآن يمكنك الضغط على الزر أدناه لتنزيل الفيديو الخاص بك فوراً:",
        reply_markup=reply_markup
    )

async def send_final_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if user_id not in USER_URLS:
        await query.answer("⚠️ انتهت صلاحية الجلسة، يرجى إرسال رابط تيك توك من جديد.", show_alert=True)
        return

    url = USER_URLS[user_id]
    
    status_msg = await query.message.edit_text("⏳ جاري استخراج وإرسال الفيديو...")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }

    try:
        async with httpx.AsyncClient(timeout=30.0, verify=False, follow_redirects=True, headers=headers) as client:
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
                    
                    # إرسال الفيديو النهائي للمستخدم
                    await context.bot.send_video(
                        chat_id=query.message.chat_id,
                        video=play_url, 
                        caption="✅ تفضل فيديو تيك توك الخاص بك بدون علامة مائية! 🚀\n\n💻 **المطور:** wd wil"
                    )
                    
                    # حذف الرابط المخزن بعد الاستخدام
                    del USER_URLS[user_id]
                    return

            await status_msg.edit_text("❌ تعذر استخراج رابط الفيديو. تأكد من صحة الرابط وجرب إرساله مرة أخرى.")

    except Exception as e:
        logging.error(f"Error handling request: {e}")
        await status_msg.edit_text("❌ حدث خطأ أثناء التحميل. تأكد من صحة الرابط أو حاول لاحقاً.")

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(check_subscription_button, pattern="^check_sub$"))
    app.add_handler(CallbackQueryHandler(show_download_button, pattern="^show_download_btn$"))
    app.add_handler(CallbackQueryHandler(send_final_version := send_final_video, pattern="^get_final_video$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_tiktok_message))
    
    app.run_polling()

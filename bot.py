import logging
import asyncio
import httpx
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.error import TelegramError

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

BOT_TOKEN = "8922544964:AAHreUn_UkIamBmtvNi5uyaGpd6qvfEq3LY"

# ضع معرف قناتك هنا (مثلاً: @YourChannelName)
MY_CHANNEL = "@my_tiktok_channel_4"

AD_LINK = "https://www.profitableratecpmnetwork.com/kc0ukqgr?key=265d6e72d7a3c187616e16bce28bf1aa"

USER_URLS = {}

async def is_user_subscribed(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=MY_CHANNEL, user_id=user_id)
        if member.status in ['left', 'kicked']:
            return False
    except TelegramError as e:
        logging.error(f"Failed to check membership for channel {MY_CHANNEL}: {e}")
        return False
    return True

def get_subscribe_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("📢 اشترك في قناتنا الرسمية", url=f"https://t.me/{MY_CHANNEL.replace('@', '')}")],
        [InlineKeyboardButton("✅ اشتركت، تحقق الآن", callback_data="check_sub")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_user_subscribed(user_id, context):
        await update.message.reply_text(
            "⚠️ لاستخدام البوت، يجب عليك الاشتراك في قناتنا أولاً:",
            reply_markup=get_subscribe_keyboard()
        )
        return

    await update.message.reply_text(
        f"أهلاً بك {update.effective_user.first_name}! 👋\n\n"
        "أرسل لي أي رابط فيديو من TikTok وسأقوم بتجهيزه لك فوراً!\n\n"
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
    
    if not await is_user_subscribed(user_id, context):
        await update.message.reply_text(
            "⚠️️ عذراً، يجب عليك الاشتراك في قناتنا أولاً لاستخدام البوت:",
            reply_markup=get_subscribe_keyboard()
        )
        return

    url = update.message.text.strip()
    if "tiktok.com" not in url:
        return

    USER_URLS[user_id] = url

    # الخطوة الأولى: زر مشاهدة الإعلان فقط
    keyboard = [
        [InlineKeyboardButton("🔗 اضغط هنا لمشاهدة الإعلان لتحميل الفيديو", url=AD_LINK)],
        [InlineKeyboardButton("✅ شاهدت الإعلان، المتابعة", callback_data="show_download_btn")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "📌 **خطوة واحدة لتحميل الفيديو:**\n\n"
        "1. اضغط على زر مشاهدة الإعلان أعلاه.\n"
        "2. ثم اضغط على زر المتابعة بالأسفل:",
        reply_markup=reply_markup
    )

async def handle_show_download_btn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if user_id not in USER_URLS:
        await query.answer("⚠️ انتهت صلاحية الجلسة، يرجى إرسال الرابط من جديد.", show_alert=True)
        return

    # الخطوة الثانية: إظهار زر "اضغط هنا لفتح رابط التحميل"
    keyboard = [
        [InlineKeyboardButton("📥 اضغط هنا لفتح رابط التحميل", callback_data="process_download")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.edit_text(
        "✅ شكراً لك على مشاهدة الإعلان!\n\n"
        "اضغط على الزر أدناه لبدء استلام الفيديو:",
        reply_markup=reply_markup
    )

async def handle_process_download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if user_id not in USER_URLS:
        await query.answer("⚠️ انتهت صلاحية الجلسة، يرجى إرسال الرابط من جديد.", show_alert=True)
        return

    url = USER_URLS[user_id]

    # حذف الأزرار وتأخير 7 ثوانٍ في الخلفية دون أي رسائل نصية مزعجة
    await query.message.delete()
    await asyncio.sleep(7)

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
                        
                    await context.bot.send_video(
                        chat_id=query.message.chat_id,
                        video=play_url, 
                        caption="✅ تفضل فيديو تيك توك الخاص بك بدون علامة مائية! 🚀\n\n💻 **المطور:** wd wil"
                    )
                    
                    del USER_URLS[user_id]
                    return

            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text="❌ تعذر استخراج رابط الفيديو. تأكد من صحة الرابط وجرب إرساله مرة أخرى."
            )

    except Exception as e:
        logging.error(f"Error handling request: {e}")
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="❌ حدث خطأ أثناء التحميل. تأكد من صحة الرابط أو حاول لاحقاً."
        )

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(check_subscription_button, pattern="^check_sub$"))
    app.add_handler(CallbackQueryHandler(handle_show_download_btn, pattern="^show_download_btn$"))
    app.add_handler(CallbackQueryHandler(handle_process_download, pattern="^process_download$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_tiktok_message))
    
    app.run_polling()

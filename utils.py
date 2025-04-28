# handlers/utils.py
import datetime
from telegram import ReplyKeyboardMarkup
import database

# دکمه‌های عمومی
BUTTON_MAIN_MENU = "🔙 بازگشت"
BUTTON_CANCEL = "🔙 بازگشت به منوی اصلی"
BUTTON_CHECK_MEMBERSHIP = "🔄 بررسی عضویت"
BUTTON_FORCED_MEMBERSHIP_SETTINGS = "⚙️ تنظیمات عضویت اجباری"  # جهت مدیریت (این دکمه در منوی اصلی استفاده نمی‌شود)

def get_main_menu_keyboard():
    """ایجاد صفحه کلید منوی اصلی با دکمه‌های صحیح"""
    keyboard = [
        ["👥 اضافه کردن عضو", "💰 جمع‌آوری سکه"],
        ["📊 مشاهده سفارش‌ها"],
        ["💳 موجودی من", "💵 خرید سکه"],
        ["زیر مجموعه گیری"],  # دکمه زیرمجموعه‌گیری بازگردانده شد
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def send_main_menu(update, context):
    """نمایش منوی اصلی فقط برای کاربران تایید‌شده"""
    user_id = update.effective_user.id
    if await check_forced_subscription(update, context, user_id):
        # اگر کاربر هنوز عضو نشده باشد، از ارسال منوی اصلی جلوگیری می‌شود.
        return
    await update.message.reply_text("🏠 منوی اصلی:", reply_markup=get_main_menu_keyboard())

async def check_forced_subscription(update, context, user_id):
    """
    بررسی عضویت اجباری:
      - ابتدا لیست کانال‌های فعال اجباری دریافت می‌شود.
      - برای هر کانال، وضعیت محدودیت زمانی یا تعداد بررسی می‌شود؛ در صورت منقضی شدن، کانال حذف می‌شود.
      - سپس وضعیت عضویت کاربر در کانال‌های باقیمانده بررسی شده و در صورت عدم عضویت کاربر، پیام درخواست عضویت ارسال می‌شود.
      - در این تابع، اعلان مدیر صرفاً حذف شده و فقط پیام نهایی به کاربر ارسال می‌شود.
    """
    active_channels = database.get_active_forced_channels()
    valid_channels = []
    now = datetime.datetime.now()

    for channel in active_channels:
        channel_username = channel["channel_username"]
        limit_type = channel["limit_type"]
        limit_value = channel["limit_value"]

        if limit_type == "time":
            try:
                expiration = datetime.datetime.fromisoformat(limit_value)
            except ValueError:
                continue
            if now < expiration:
                valid_channels.append(channel)
            else:
                database.remove_forced_channel(channel_username)
                # اعلان پایان عضویت برای مدیر در اینجا حذف شده است.
        elif limit_type == "members":
            try:
                required_members = int(limit_value)
                current_members = int(channel.get("current_members", "0"))
            except ValueError:
                continue
            if current_members < required_members:
                valid_channels.append(channel)
            else:
                database.remove_forced_channel(channel_username)
                # اعلان پایان عضویت برای مدیر حذف شده است.

    # اگر هیچ کانال عضویت اجباری فعال وجود نداشته باشد، کاربر بدون محدودیت وارد می‌شود.
    if not valid_channels:
        return False

    not_joined = []
    for channel in valid_channels:
        channel_username = channel["channel_username"]
        try:
            member = await context.bot.get_chat_member(chat_id=channel_username, user_id=user_id)
            if member.status not in ["member", "administrator", "creator"]:
                not_joined.append(channel_username)
        except Exception:
            not_joined.append(channel_username)

    if not_joined:
        message = "❗ لطفاً ابتدا در کانال‌های زیر عضو شوید:\n" + "\n".join(not_joined)
        message += "\n\n🔄 پس از عضویت، روی دکمه 'بررسی عضویت' کلیک کنید."
        keyboard = ReplyKeyboardMarkup([[BUTTON_CHECK_MEMBERSHIP]], resize_keyboard=True)
        await update.message.reply_text(message, reply_markup=keyboard)
        return True

    return False

async def confirm_membership(update, context):
    """
    بررسی مجدد عضویت پس از کلیک کاربر روی دکمه 'بررسی عضویت'
    و ثبت عضو شدن در کانال‌های اجباری. همچنین تعداد اعضای ثبت‌شده افزایش می‌یابد.
    در این نسخه هیچ پیغام به مدیر ارسال نمی‌شود؛ فقط پیام نهایی به کاربر ارسال می‌شود.
    """
    user_id = update.effective_user.id
    active_channels = database.get_active_forced_channels()
    successfully_joined = []

    for channel in active_channels:
        channel_username = channel["channel_username"]
        try:
            member = await context.bot.get_chat_member(chat_id=channel_username, user_id=user_id)
            if member.status in ["member", "administrator", "creator"]:
                if not database.is_user_joined_forced_channel(user_id, channel_username):
                    database.add_joined_channel(user_id, channel_username, join_type="forced")
                    database.increment_forced_channel_count(channel_username)
                    successfully_joined.append(channel_username)
        except Exception:
            pass

    if successfully_joined:
        # در اینجا اعلان به مدیر حذف شده است؛ فقط پیام نهایی به کاربر ارسال می‌شود.
        message = "✅ شما در کانال‌های زیر عضو شدید:\n" + "\n".join(successfully_joined)
        message += "\n\n🏠 حالا می‌توانید از ربات استفاده کنید."
        await update.message.reply_text(message)
        await send_main_menu(update, context)
    else:
        await update.message.reply_text(
            "❌ شما هنوز عضو کانال‌های موردنیاز نشده‌اید. لطفاً عضو شوید و دوباره تلاش کنید!"
        )

# تابع notify_admin حذف شده است؛ بنابراین هیچ پیغامی به مدیر ارسال نخواهد شد.
# def notify_admin(context, message):
#     ...

def register_force_check_handler(app):
    """ثبت هندلر برای دکمه بررسی عضویت"""
    from telegram.ext import MessageHandler, filters
    app.add_handler(MessageHandler(filters.Regex(f"^{BUTTON_CHECK_MEMBERSHIP}$"), confirm_membership))
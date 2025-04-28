from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ConversationHandler
import config
import database
import asyncio

# ثبت هندلرها
from handlers.start import register_start_handler
from handlers.admin import register_admin_handler
from handlers.subscriber import register_subscriber_handler
from handlers.coin_collection import register_coin_collection_handler
from handlers.coin_balance import register_coin_balance_handler
from handlers.buy_coins import register_buy_coins_handler
from handlers.orders import register_view_orders_handler
from handlers.referral import register_referral_handler
from handlers.sample_conversation import register_conversation_handler
from handlers.help import register_help_handler
from handlers.admin_order_reply import register_admin_order_reply_handler
from handlers.utils import send_main_menu, register_force_check_handler
from handlers.forced_membership import register_forced_membership_handler  # 🔹 افزوده شد

app = Flask(__name__)

# مقداردهی اولیه دیتابیس
try:
    database.init_db()
except AttributeError:
    print("خطا: تابع init_db پیدا نشد.")

# ساخت اپلیکیشن تلگرام
bot_app = ApplicationBuilder().token(config.BOT_TOKEN).build()

# ثبت هندلرهای ربات
register_start_handler(bot_app)
register_admin_handler(bot_app)
register_subscriber_handler(bot_app)
register_coin_collection_handler(bot_app)
register_coin_balance_handler(bot_app)
register_buy_coins_handler(bot_app)
register_view_orders_handler(bot_app)
register_referral_handler(bot_app)
register_conversation_handler(bot_app)
register_help_handler(bot_app)
register_admin_order_reply_handler(bot_app)
register_force_check_handler(bot_app)
register_forced_membership_handler(bot_app)  # 🔹 افزوده شد

# لغو گفتگو به صورت سراسری
async def global_cancel(update, context):
    context.user_data.clear()
    await send_main_menu(update, context)
    return ConversationHandler.END

bot_app.add_handler(CommandHandler("cancel", global_cancel))

@app.route(f"/{config.BOT_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot_app.bot)

    async def handle():
        if not getattr(bot_app, "_initialized", False):  # 🔹 بررسی مقداردهی اولیه
            await bot_app.initialize()
        await bot_app.process_update(update)

    loop = asyncio.get_event_loop()

    if loop.is_running():
        asyncio.ensure_future(handle())
    else:
        loop.run_until_complete(handle())

    return "OK"

@app.route('/')
def home():
    return "ربات فعال است!"

if __name__ == "__main__":
    bot_app.run_webhook(
        listen="0.0.0.0",
        port=5000,
        webhook_url=f"https://{config.PYTHONANYWHERE_DOMAIN}/{config.BOT_TOKEN}"
    )
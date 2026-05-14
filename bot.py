import logging
from telegram import Update, BotCommand
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes,
)
from config import BOT_TOKEN, WORKERS_GROUP_ID
from db import init_db
from start import (
    start_handler, help_handler, clear_handler,
    contact_command, services_command,
)
from admin import (
    admin_command, analytics_command, admin_callback, testgroup_command
)
from callbacks import menu_callback
from order import order_conversation_handler

logging.basicConfig(
    format="%(asctime)s — %(name)s — %(levelname)s — %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

_last_action: dict[int, float] = {}
ANTI_SPAM_SECS = 3

PRIVATE = filters.ChatType.PRIVATE


async def anti_spam_check(update: Update) -> bool:
    import time
    user_id = update.effective_user.id
    now = time.time()
    if now - _last_action.get(user_id, 0) < ANTI_SPAM_SECS:
        return False
    _last_action[user_id] = now
    return True


async def unknown_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    if not await anti_spam_check(update):
        await update.message.reply_text("⚠️ Please slow down. Use the menu buttons.")
        return
    from db import get_user_language
    from strings import t
    from keyboards import main_menu_keyboard
    user = update.effective_user
    lang = await get_user_language(user.id)
    await update.message.reply_text(
        t(lang, "welcome"),
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard(lang),
    )


async def set_commands(app: Application):
    commands = [
        BotCommand("start",     "🏠 Main menu"),
        BotCommand("services",  "💼 Browse our services"),
        BotCommand("order",     "📋 Place a service request"),
        BotCommand("contact",   "📬 Contact & social links"),
        BotCommand("help",      "❓ Help & commands"),
        BotCommand("clear",     "🧹 Clear conversation"),
        BotCommand("admin",     "🔐 Admin panel"),
        BotCommand("analytics", "📊 Analytics dashboard"),
        BotCommand("testgroup", "🔧 Test workers group connection"),
    ]
    await app.bot.set_my_commands(commands)
    logger.info("Bot commands registered.")


async def validate_workers_group(app: Application):
    """Check workers group connection at startup and log the result."""
    try:
        chat = await app.bot.get_chat(WORKERS_GROUP_ID)
        logger.info(f"✅ Workers group OK: '{chat.title}' (ID: {WORKERS_GROUP_ID})")
    except Exception as e:
        logger.warning(
            f"⚠️  Workers group NOT reachable (ID: {WORKERS_GROUP_ID}): {e}\n"
            f"    → Add the bot to the workers group, then run /testgroup as admin."
        )


async def post_init(app: Application):
    await init_db()
    await set_commands(app)
    await validate_workers_group(app)
    logger.info("✅ OBINHO AI bot initialized and ready.")


def build_app() -> Application:
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    app.add_handler(order_conversation_handler())

    app.add_handler(CommandHandler("start",     start_handler,     filters=PRIVATE))
    app.add_handler(CommandHandler("help",      help_handler,      filters=PRIVATE))
    app.add_handler(CommandHandler("clear",     clear_handler,     filters=PRIVATE))
    app.add_handler(CommandHandler("contact",   contact_command,   filters=PRIVATE))
    app.add_handler(CommandHandler("services",  services_command,  filters=PRIVATE))
    app.add_handler(CommandHandler("admin",     admin_command,     filters=PRIVATE))
    app.add_handler(CommandHandler("analytics", analytics_command, filters=PRIVATE))
    app.add_handler(CommandHandler("testgroup", testgroup_command, filters=PRIVATE))

    app.add_handler(CallbackQueryHandler(admin_callback, pattern=r"^admin_"))
    app.add_handler(CallbackQueryHandler(menu_callback))

    app.add_handler(MessageHandler(PRIVATE & filters.TEXT & ~filters.COMMAND, unknown_message))

    return app


def run():
    app = build_app()
    logger.info("🚀 Starting OBINHO AI bot (middleman mode)...")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    run()

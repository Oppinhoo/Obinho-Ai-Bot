import logging
from telegram import Update
from telegram.ext import ContextTypes
from obinho_bot.database.db import get_all_stats, get_user_language
from obinho_bot.locales.strings import t
from obinho_bot.utils.keyboards import admin_keyboard, main_menu_keyboard
from obinho_bot.config import ADMIN_IDS, WORKERS_GROUP_ID

logger = logging.getLogger(__name__)


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def _build_stats_text(stats: dict) -> str:
    top_services = "\n".join(
        f"  {i+1}. {s[0]}: *{s[1]}* requests"
        for i, s in enumerate(stats["top_services"])
    ) or "  No requests yet"
    lang_stats = "\n".join(
        f"  • {l[0].upper()}: {l[1]} users"
        for l in stats["language_stats"]
    ) or "  No data"
    return (
        "📊 *OBINHO AI — Analytics Dashboard*\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👥 *Total Users:* {stats['total_users']}\n"
        f"📋 *Total Requests:* {stats['total_requests']}\n"
        f"⏳ *Pending Requests:* {stats['pending_requests']}\n\n"
        f"📈 *Top Services:*\n{top_services}\n\n"
        f"🌍 *Language Distribution:*\n{lang_stats}\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "_Updated in real-time_"
    )


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = await get_user_language(user.id)
    if not is_admin(user.id):
        await update.message.reply_text(t(lang, "not_admin"))
        return
    stats = await get_all_stats()
    await update.message.reply_text(
        _build_stats_text(stats),
        parse_mode="Markdown",
        reply_markup=admin_keyboard(),
    )


async def analytics_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = await get_user_language(user.id)
    if not is_admin(user.id):
        await update.message.reply_text(t(lang, "not_admin"))
        return
    stats = await get_all_stats()
    await update.message.reply_text(
        _build_stats_text(stats),
        parse_mode="Markdown",
        reply_markup=admin_keyboard(),
    )


async def testgroup_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to verify workers group connection."""
    user = update.effective_user
    lang = await get_user_language(user.id)
    if not is_admin(user.id):
        await update.message.reply_text(t(lang, "not_admin"))
        return

    await update.message.reply_text(
        f"🔍 Testing workers group connection...\n"
        f"Group ID: `{WORKERS_GROUP_ID}`",
        parse_mode="Markdown",
    )

    try:
        chat = await context.bot.get_chat(WORKERS_GROUP_ID)
        test_msg = await context.bot.send_message(
            chat_id=WORKERS_GROUP_ID,
            text=(
                "✅ *OBINHO AI — Connection Test*\n\n"
                "Workers group is connected successfully!\n"
                "Client requests will be forwarded here automatically."
            ),
            parse_mode="Markdown",
        )
        await update.message.reply_text(
            f"✅ *Workers group connected!*\n\n"
            f"📛 Group name: *{chat.title}*\n"
            f"🆔 Group ID: `{WORKERS_GROUP_ID}`\n"
            f"👥 Type: {chat.type}\n\n"
            f"A test message was sent to the group.",
            parse_mode="Markdown",
        )
        logger.info(f"Workers group test successful: {chat.title} ({WORKERS_GROUP_ID})")
    except Exception as e:
        error_str = str(e)
        logger.error(f"Workers group test failed: {error_str}")

        if "Chat not found" in error_str:
            advice = (
                "❌ *Chat not found.*\n\n"
                "To fix this:\n"
                "1️⃣ Add the bot to your workers Telegram group\n"
                "2️⃣ In the group, send any message — then forward it to @userinfobot to get the group ID\n"
                "3️⃣ The group ID must be a *negative number* (e.g. `-1001234567890`)\n"
                "4️⃣ Update `WORKERS_GROUP_ID` in your Replit Secrets with the correct ID\n"
                "5️⃣ Restart the bot and run `/testgroup` again"
            )
        elif "bot is not a member" in error_str or "kicked" in error_str:
            advice = (
                "❌ *Bot is not in the group.*\n\n"
                "To fix this:\n"
                "1️⃣ Open your workers Telegram group\n"
                "2️⃣ Tap the group name → Add Members\n"
                "3️⃣ Search for your bot and add it\n"
                "4️⃣ Run `/testgroup` again to verify"
            )
        elif "Forbidden" in error_str:
            advice = (
                "❌ *Bot was blocked or lacks permission.*\n\n"
                "To fix this:\n"
                "1️⃣ Make sure the bot is still a member of the group\n"
                "2️⃣ Make the bot an admin in the group for reliable delivery\n"
                "3️⃣ Run `/testgroup` again"
            )
        else:
            advice = f"❌ *Error:* `{error_str}`"

        await update.message.reply_text(advice, parse_mode="Markdown")


async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = update.effective_user
    if not is_admin(user.id):
        await query.answer("❌ Admin access required.", show_alert=True)
        return
    stats = await get_all_stats()
    await query.edit_message_text(
        _build_stats_text(stats),
        parse_mode="Markdown",
        reply_markup=admin_keyboard(),
    )

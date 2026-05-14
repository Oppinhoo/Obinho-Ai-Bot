from telegram import Update
from telegram.ext import ContextTypes
from obinho_bot.database.db import upsert_user, get_user_language, log_event
from obinho_bot.locales.strings import t
from obinho_bot.utils.keyboards import main_menu_keyboard, contact_keyboard


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = await get_user_language(user.id)
    await upsert_user(user.id, user.username or "", user.full_name or "", lang)
    await log_event("start", user.id)
    await update.message.reply_text(
        t(lang, "welcome"),
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard(lang),
    )


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = await get_user_language(user.id)
    await update.message.reply_text(
        t(lang, "help_text"),
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard(lang),
    )


async def clear_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    user = update.effective_user
    lang = await get_user_language(user.id)
    await update.message.reply_text(
        "🧹 Conversation cleared!\n\n" + t(lang, "welcome"),
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard(lang),
    )


async def contact_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = await get_user_language(user.id)
    await update.message.reply_text(
        t(lang, "contact_menu"),
        parse_mode="Markdown",
        reply_markup=contact_keyboard(),
    )


async def services_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from obinho_bot.utils.keyboards import services_keyboard
    user = update.effective_user
    lang = await get_user_language(user.id)
    await log_event("view_services", user.id)
    await update.message.reply_text(
        t(lang, "services_menu"),
        parse_mode="Markdown",
        reply_markup=services_keyboard(),
    )

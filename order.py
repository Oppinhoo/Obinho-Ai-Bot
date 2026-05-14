import logging
from datetime import datetime
from telegram import Update
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler,
    MessageHandler, CallbackQueryHandler, filters,
)
from obinho_bot.database.db import (
    get_user_language, save_request, count_recent_requests, log_event
)
from obinho_bot.locales.strings import t
from obinho_bot.utils.keyboards import main_menu_keyboard, order_service_keyboard, confirm_keyboard
from obinho_bot.utils.helpers import generate_request_id, format_worker_message, validate_whatsapp, sanitize_text
from obinho_bot.config import SERVICES, WORKERS_GROUP_ID, MAX_REQUESTS_PER_HOUR, ADMIN_IDS

logger = logging.getLogger(__name__)

ASK_NAME, ASK_WHATSAPP, ASK_SERVICE, ASK_DETAILS, CONFIRM = range(5)

PRIVATE = filters.ChatType.PRIVATE


async def order_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = await get_user_language(user.id)

    count = await count_recent_requests(user.id, 3600)
    if count >= MAX_REQUESTS_PER_HOUR:
        msg = t(lang, "max_requests")
        if update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(msg, parse_mode="Markdown")
        else:
            await update.message.reply_text(msg, parse_mode="Markdown")
        return ConversationHandler.END

    context.user_data.clear()
    context.user_data["lang"] = lang
    msg = t(lang, "order_start")

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(msg, parse_mode="Markdown")
    else:
        await update.message.reply_text(msg, parse_mode="Markdown")

    return ASK_NAME


async def received_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "en")
    name = sanitize_text(update.message.text, 100)
    if len(name) < 2:
        await update.message.reply_text("⚠️ Please enter a valid full name (at least 2 characters).")
        return ASK_NAME
    context.user_data["client_name"] = name
    await update.message.reply_text(t(lang, "ask_whatsapp"), parse_mode="Markdown")
    return ASK_WHATSAPP


async def received_whatsapp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "en")
    number = update.message.text.strip()
    if not validate_whatsapp(number):
        await update.message.reply_text(
            "⚠️ Please enter a valid WhatsApp number with country code.\n"
            "Example: +252612345678"
        )
        return ASK_WHATSAPP
    context.user_data["whatsapp"] = number
    await update.message.reply_text(
        t(lang, "ask_service"),
        parse_mode="Markdown",
        reply_markup=order_service_keyboard(),
    )
    return ASK_SERVICE


async def service_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get("lang", "en")
    idx = int(query.data.split("_")[-1])
    context.user_data["service"] = SERVICES[idx]
    await query.edit_message_text(t(lang, "ask_details"), parse_mode="Markdown")
    return ASK_DETAILS


async def received_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "en")
    details = sanitize_text(update.message.text, 2000)
    if len(details) < 10:
        await update.message.reply_text(
            "⚠️ Please describe your project in more detail (at least 10 characters)."
        )
        return ASK_DETAILS
    context.user_data["details"] = details

    name = context.user_data["client_name"]
    whatsapp = context.user_data["whatsapp"]
    service = context.user_data["service"]

    await update.message.reply_text(
        t(lang, "confirm_request", name=name, whatsapp=whatsapp, service=service, details=details),
        parse_mode="Markdown",
        reply_markup=confirm_keyboard(lang),
    )
    return CONFIRM


async def _notify_admins_of_failure(context: ContextTypes.DEFAULT_TYPE, request_id: str, error: str):
    """Silently notify admins if workers group forwarding fails."""
    notice = (
        f"⚠️ *Forwarding Failed*\n\n"
        f"Request `{request_id}` could not be sent to the workers group.\n\n"
        f"*Error:* `{error}`\n\n"
        f"👉 Run `/testgroup` to diagnose the connection."
    )
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=notice,
                parse_mode="Markdown",
            )
        except Exception:
            pass


async def confirm_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get("lang", "en")
    user = update.effective_user

    if query.data == "cancel_request":
        context.user_data.clear()
        await query.edit_message_text(
            t(lang, "cancelled"),
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard(lang),
        )
        return ConversationHandler.END

    request_id = generate_request_id()
    name = context.user_data["client_name"]
    whatsapp = context.user_data["whatsapp"]
    service = context.user_data["service"]
    details = context.user_data["details"]

    await save_request(request_id, user.id, name, whatsapp, service, details, lang)

    now = datetime.utcnow()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M UTC")

    worker_msg = (
        "🚨 *NEW CLIENT REQUEST — OBINHO AI*\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👤 *Name:* {name}\n"
        f"💼 *Service:* {service}\n"
        f"📱 *WhatsApp:* `{whatsapp}`\n"
        f"📝 *Details:*\n{details}\n\n"
        f"📅 *Date:* {date_str}\n"
        f"🕒 *Time:* {time_str}\n"
        f"🆔 *Request ID:* `{request_id}`\n"
        f"🌍 *Language:* {lang.upper()}\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "⚡ _Contact the client on WhatsApp ASAP._"
    )

    forward_ok = False
    try:
        await context.bot.send_message(
            chat_id=WORKERS_GROUP_ID,
            text=worker_msg,
            parse_mode="Markdown",
        )
        forward_ok = True
        logger.info(f"✅ Request {request_id} forwarded to workers group {WORKERS_GROUP_ID}.")
    except Exception as e:
        error_str = str(e)
        logger.error(f"❌ Failed to forward {request_id} to group {WORKERS_GROUP_ID}: {error_str}")
        await _notify_admins_of_failure(context, request_id, error_str)

    await log_event("request_submitted", user.id, f"{service}:{request_id}:forwarded={forward_ok}")
    context.user_data.clear()
    await query.edit_message_text(
        t(lang, "request_submitted", request_id=request_id),
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard(lang),
    )
    return ConversationHandler.END


async def cancel_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = await get_user_language(user.id)
    context.user_data.clear()
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            t(lang, "cancelled"),
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard(lang),
        )
    else:
        await update.message.reply_text(
            t(lang, "cancelled"),
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard(lang),
        )
    return ConversationHandler.END


def order_conversation_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CommandHandler("order", order_start, filters=PRIVATE),
            CallbackQueryHandler(order_start, pattern="^start_order$"),
        ],
        states={
            ASK_NAME:     [MessageHandler(PRIVATE & filters.TEXT & ~filters.COMMAND, received_name)],
            ASK_WHATSAPP: [MessageHandler(PRIVATE & filters.TEXT & ~filters.COMMAND, received_whatsapp)],
            ASK_SERVICE:  [CallbackQueryHandler(service_selected, pattern=r"^order_service_\d+$")],
            ASK_DETAILS:  [MessageHandler(PRIVATE & filters.TEXT & ~filters.COMMAND, received_details)],
            CONFIRM:      [CallbackQueryHandler(confirm_request, pattern="^(confirm_request|cancel_request)$")],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_order, filters=PRIVATE),
            CommandHandler("start",  cancel_order, filters=PRIVATE),
            CallbackQueryHandler(cancel_order, pattern="^cancel_order_cmd$"),
        ],
        allow_reentry=True,
        per_message=False,
    )

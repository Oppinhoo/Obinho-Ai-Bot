from telegram import Update
from telegram.ext import ContextTypes
from obinho_bot.database.db import (
    get_user_language, update_user_language, get_user_requests, log_event
)
from obinho_bot.locales.strings import t
from obinho_bot.utils.keyboards import (
    main_menu_keyboard, services_keyboard,
    contact_keyboard, language_keyboard,
)


async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = update.effective_user
    lang = await get_user_language(user.id)
    data = query.data

    if data == "back_main":
        await query.edit_message_text(
            t(lang, "welcome"),
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard(lang),
        )

    elif data == "menu_services":
        await query.edit_message_text(
            t(lang, "services_menu"),
            parse_mode="Markdown",
            reply_markup=services_keyboard(),
        )

    elif data == "menu_contact":
        await query.edit_message_text(
            t(lang, "contact_menu"),
            parse_mode="Markdown",
            reply_markup=contact_keyboard(),
        )

    elif data == "menu_language":
        await query.edit_message_text(
            t(lang, "language_select"),
            parse_mode="Markdown",
            reply_markup=language_keyboard(),
        )

    elif data == "menu_help":
        await query.edit_message_text(
            t(lang, "help_text"),
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard(lang),
        )

    elif data == "menu_my_requests":
        rows = await get_user_requests(user.id)
        if not rows:
            text = t(lang, "no_requests")
        else:
            text = t(lang, "my_requests")
            for req_id, service, status, created_at in rows:
                date = created_at[:10] if created_at else "N/A"
                status_icon = "✅" if status == "done" else "⏳"
                text += f"{status_icon} `{req_id}` — {service} ({date})\n"
        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard(lang),
        )

    elif data.startswith("lang_"):
        new_lang = data.split("_")[1]
        await update_user_language(user.id, new_lang)
        await log_event("language_change", user.id, new_lang)
        confirmations = {
            "en": "✅ Language set to English!",
            "so": "✅ Luqadda waxaa loo dejiyay Somali!",
            "ar": "✅ تم تعيين اللغة إلى العربية!",
        }
        await query.edit_message_text(
            confirmations.get(new_lang, "✅ Language updated!") + "\n\n" + t(new_lang, "welcome"),
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard(new_lang),
        )

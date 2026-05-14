from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from obinho_bot.config import SERVICES, SOCIAL_LINKS
from obinho_bot.locales.strings import t


def main_menu_keyboard(lang: str) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton("💼 Request a Service", callback_data="start_order"),
            InlineKeyboardButton("📋 My Requests", callback_data="menu_my_requests"),
        ],
        [
            InlineKeyboardButton("📬 Contact Us", callback_data="menu_contact"),
            InlineKeyboardButton("🌍 Language", callback_data="menu_language"),
        ],
        [
            InlineKeyboardButton("❓ Help", callback_data="menu_help"),
        ],
    ]
    return InlineKeyboardMarkup(buttons)


def services_keyboard() -> InlineKeyboardMarkup:
    buttons = []
    row = []
    for i, service in enumerate(SERVICES):
        row.append(InlineKeyboardButton(service, callback_data=f"order_service_{i}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("⬅️ Back", callback_data="back_main")])
    return InlineKeyboardMarkup(buttons)


def confirm_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(t(lang, "confirm"), callback_data="confirm_request"),
            InlineKeyboardButton(t(lang, "cancel"), callback_data="cancel_request"),
        ]
    ])


def language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
            InlineKeyboardButton("🇸🇴 Somali", callback_data="lang_so"),
            InlineKeyboardButton("🇸🇦 Arabic", callback_data="lang_ar"),
        ],
        [InlineKeyboardButton("⬅️ Back", callback_data="back_main")]
    ])


def contact_keyboard() -> InlineKeyboardMarkup:
    icons = {
        "WhatsApp": "💬", "TikTok": "🎵", "Facebook": "📘",
        "Instagram": "📸", "YouTube": "▶️", "Telegram": "✈️",
    }
    buttons = []
    row = []
    for platform, url in SOCIAL_LINKS.items():
        icon = icons.get(platform, "🔗")
        row.append(InlineKeyboardButton(f"{icon} {platform}", url=url))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("⬅️ Back", callback_data="back_main")])
    return InlineKeyboardMarkup(buttons)


def order_service_keyboard() -> InlineKeyboardMarkup:
    buttons = []
    row = []
    for i, service in enumerate(SERVICES):
        row.append(InlineKeyboardButton(service, callback_data=f"order_service_{i}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel_order_cmd")])
    return InlineKeyboardMarkup(buttons)


def admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📊 Full Analytics", callback_data="admin_analytics"),
            InlineKeyboardButton("🔄 Refresh", callback_data="admin_refresh"),
        ],
    ])

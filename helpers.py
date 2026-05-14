import uuid
import re
from datetime import datetime


def generate_request_id() -> str:
    return "OBN-" + uuid.uuid4().hex[:8].upper()


def format_datetime():
    now = datetime.utcnow()
    return now.strftime("%Y-%m-%d"), now.strftime("%H:%M UTC")


def detect_language(text: str) -> str:
    arabic_pattern = re.compile(r'[\u0600-\u06FF]')
    somali_words = {"waa", "ma", "ku", "si", "ah", "ka", "oo", "iyo", "ee", "la"}
    if arabic_pattern.search(text):
        return "ar"
    words = set(text.lower().split())
    if len(words & somali_words) >= 2:
        return "so"
    return "en"


def format_worker_message(client_name: str, whatsapp: str, service: str,
                           details: str, request_id: str, language: str,
                           user_id: int) -> str:
    date_str, time_str = format_datetime()
    return (
        "🚨 *NEW CLIENT REQUEST — OBINHO AI*\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👤 *Name:* {client_name}\n"
        f"💼 *Service:* {service}\n"
        f"📱 *WhatsApp:* {whatsapp}\n"
        f"📝 *Details:*\n{details}\n\n"
        f"📅 *Date:* {date_str}\n"
        f"🕒 *Time:* {time_str}\n"
        f"🆔 *Request ID:* `{request_id}`\n"
        f"🌍 *Language:* {language.upper()}\n"
        f"🤖 *Telegram ID:* `{user_id}`\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "⚡ _Please contact the client on WhatsApp ASAP._"
    )


def validate_whatsapp(number: str) -> bool:
    cleaned = re.sub(r'[\s\-\(\)]', '', number)
    return bool(re.match(r'^\+?[1-9]\d{7,14}$', cleaned))


def sanitize_text(text: str, max_len: int = 1000) -> str:
    return text.strip()[:max_len]

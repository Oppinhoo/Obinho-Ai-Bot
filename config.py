import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
WORKERS_GROUP_ID = int(os.environ["WORKERS_GROUP_ID"])
ADMIN_IDS = [int(x.strip()) for x in os.environ.get("ADMIN_IDS", "").split(",") if x.strip()]

DB_PATH = "obinho_bot/obinho.db"

SOCIAL_LINKS = {
    "WhatsApp": "https://wa.me/your_number",
    "TikTok": "https://tiktok.com/@obinhoai",
    "Facebook": "https://facebook.com/obinhoai",
    "Instagram": "https://instagram.com/obinhoai",
    "YouTube": "https://youtube.com/@obinhoai",
    "Telegram": "https://t.me/obinhoai",
}

SERVICES = [
    "Graphic Design",
    "Logo Design",
    "Video Editing",
    "Web Development",
    "App Development",
    "Social Media Management",
    "Business Marketing",
    "Translation",
    "Writing",
    "SEO Services",
    "UI/UX Design",
    "Animation",
    "Content Creation",
]

SUPPORTED_LANGUAGES = {
    "en": "🇬🇧 English",
    "so": "🇸🇴 Somali",
    "ar": "🇸🇦 Arabic",
}

ANTI_SPAM_SECONDS = 3
MAX_REQUESTS_PER_HOUR = 10

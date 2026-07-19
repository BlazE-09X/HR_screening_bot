import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    bot_token: str
    gemini_api_key: str
    database_path: str
    google_sheets_credentials_path: str
    google_sheet_id: str
    recruiter_ids: list[int]


def get_settings() -> Settings:
    bot_token = os.getenv("BOT_TOKEN")
    gemini_api_key = os.getenv("GEMINI_API_KEY")

    if not bot_token:
        raise ValueError("BOT_TOKEN не задан в .env файле")
    if not gemini_api_key:
        raise ValueError("GEMINI_API_KEY не задан в .env файле")

    recruiter_ids_raw = os.getenv("RECRUITER_IDS", "")
    recruiter_ids = [int(x.strip()) for x in recruiter_ids_raw.split(",") if x.strip()]

    return Settings(
        bot_token=bot_token,
        gemini_api_key=gemini_api_key,
        database_path=os.getenv("DATABASE_PATH", "data/bot.db"),
        google_sheets_credentials_path=os.getenv("GOOGLE_SHEETS_CREDENTIALS_PATH", "credentials.json"),
        google_sheet_id=os.getenv("GOOGLE_SHEET_ID", ""),
        recruiter_ids=recruiter_ids,
    )


settings = get_settings()
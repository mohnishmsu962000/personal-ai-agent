from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    app_name: str = "Personal AI Agent"
    app_version: str = "0.1.0"
    debug: bool = False

    # OpenAI
    openai_api_key: str
    openai_model: str = "gpt-4o"

    # Telegram
    telegram_bot_token: str
    telegram_allowed_user_id: int

    # Notion
    notion_api_key: str
    notion_tasks_database_id: str

    # Google Calendar
    google_calendar_id: str = "primary"
    google_credentials_path: str = "credentials.json"
    google_token_path: str = "token.json"

    # Scheduler
    daily_summary_hour: int = 8
    daily_summary_minute: int = 0

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Telegram Nail AI Manager"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"

    openai_api_key: str = Field(..., alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4.1-mini", alias="OPENAI_MODEL")
    openai_base_url: str = Field(default="https://polza.ai/api/v1", alias="OPENAI_BASE_URL")

    bot_token: str = Field(..., alias="BOT_TOKEN")
    manager_chat_id: int = Field(..., alias="MANAGER_CHAT_ID")
    telegram_webhook_path: str = Field(default="/telegram/webhook", alias="TELEGRAM_WEBHOOK_PATH")
    telegram_webhook_secret: str | None = Field(default=None, alias="TELEGRAM_WEBHOOK_SECRET")

    google_service_account_file: str = Field(..., alias="GOOGLE_SERVICE_ACCOUNT_FILE")
    google_sheet_id: str = Field(..., alias="GOOGLE_SHEET_ID")
    google_sheet_worksheet: str = Field(default="Leads", alias="GOOGLE_SHEET_WORKSHEET")

    database_url: str = Field(default="sqlite+aiosqlite:///./data/app.db", alias="DATABASE_URL")

    master_name: str = Field(default="Анна", alias="MASTER_NAME")
    work_hours: str = Field(default="пн-сб 10:00-20:00", alias="WORK_HOURS")
    studio_address: str = Field(
        default="г. Москва, ул. Примерная, 10, кабинет 5",
        alias="STUDIO_ADDRESS",
    )
    route_description: str = Field(
        default="Вход со стороны улицы, 2 этаж. Точную схему прохода отправим перед записью.",
        alias="ROUTE_DESCRIPTION",
    )
    manicure_price: str = Field(default="от 1500 руб.", alias="MANICURE_PRICE")
    pedicure_price: str = Field(default="от 2200 руб.", alias="PEDICURE_PRICE")
    gel_polish_price: str = Field(default="от 2000 руб.", alias="GEL_POLISH_PRICE")
    nail_extension_price: str = Field(default="от 3500 руб.", alias="NAIL_EXTENSION_PRICE")
    materials_info: str = Field(
        default="Базовые нюдовые, красные, молочные и сезонные оттенки обычно в наличии. По конкретному цвету лучше уточнить заранее.",
        alias="MATERIALS_INFO",
    )


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()

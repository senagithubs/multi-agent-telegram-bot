"""
core/config.py
--------------
Merkezi konfigürasyon. Tüm ayarlar tek yerden, ortam değişkenlerinden
okunur. Kod içine gizli bilgi (token, API key) gömülmez.
"""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    telegram_token: str
    openai_api_key: str | None
    openai_model: str
    database_url: str
    use_webhook: bool
    webhook_url: str | None
    webhook_port: int
    llm_enabled: bool

    @classmethod
    def from_env(cls) -> "Config":
        token = os.environ.get("TELEGRAM_BOT_TOKEN")
        if not token:
            raise RuntimeError(
                "TELEGRAM_BOT_TOKEN ayarlı değil. "
                "Önce: export TELEGRAM_BOT_TOKEN='...'"
            )
        openai_key = os.environ.get("OPENAI_API_KEY")
        return cls(
            telegram_token=token,
            openai_api_key=openai_key,
            openai_model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
            database_url=os.environ.get("DATABASE_URL", "sqlite:///bot.db"),
            use_webhook=os.environ.get("USE_WEBHOOK", "false").lower() == "true",
            webhook_url=os.environ.get("WEBHOOK_URL"),
            webhook_port=int(os.environ.get("WEBHOOK_PORT", "8443")),
            # LLM sadece API anahtarı varsa aktif olur; yoksa kural tabanlı çalışır
            llm_enabled=bool(openai_key),
        )



import logging

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class LLMAgent(BaseAgent):
    name = "assistant"

    SYSTEM_PROMPT = (
        "You are a helpful, concise assistant inside a Telegram bot. "
        "Answer clearly and briefly. If you are unsure, say so."
    )

    def __init__(self, api_key: str | None, model: str = "gpt-4o-mini"):
        self.model = model
        self.enabled = bool(api_key)
        self._client = None
        if self.enabled:
            try:
                # openai kütüphanesini sadece gerektiğinde import et
                from openai import OpenAI
                self._client = OpenAI(api_key=api_key)
            except Exception as exc:
                logger.warning("OpenAI istemcisi kurulamadı: %s", exc)
                self.enabled = False

    def can_handle(self, message: str) -> float:
        # LLM genel amaçlı bir ajandır: aktifse orta-yüksek öncelikli
        # fallback olur (uzman ajanlar hâlâ öncelikli kalır).
        return 0.5 if self.enabled else 0.0

    def handle(self, message: str, history: list[dict] | None = None) -> str:
        if not self.enabled or self._client is None:
            return "AI şu an devre dışı (API anahtarı ayarlı değil)."

        # Konuşma geçmişini OpenAI formatına çevir
        messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": message})

        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=500,
            )
            return response.choices[0].message.content.strip()
        except Exception as exc:
            logger.exception("LLM çağrısı başarısız: %s", exc)
            return (
                "AI servisine şu an ulaşamadım. "
                "Lütfen biraz sonra tekrar dene."
            )

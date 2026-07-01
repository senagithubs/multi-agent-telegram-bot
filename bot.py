

import asyncio
import logging

from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ContextTypes, filters,
)

from core import Config, Database, create_flask_app
from agents import MathAgent, EchoAgent, LLMAgent, Router

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


class BotService:
    """Botun tum bilesenlerini bir arada tutan servis sinifi."""

    def __init__(self, config: Config):
        self.config = config
        self.db = Database(config.database_url)
        # Ajanlari kur. Uzman ajanlar once, genel/fallback ajanlar sonra.
        self.router = Router(agents=[
            MathAgent(),
            LLMAgent(
                api_key=config.openai_api_key,
                model=config.openai_model,
            ),
            EchoAgent(),
        ])

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        self.db.get_or_create_user(user.id, user.username)
        await update.message.reply_text(
            "Merhaba! Ben cok-ajanli bir asistan botuyum. "
            "Matematik islemi yazabilir, soru sorabilirsin. "
            "/help ile komutlari gor."
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        agents = ", ".join(self.router.list_agents())
        await update.message.reply_text(
            "Yapabildiklerim:\n"
            "- Matematik: 12 * (3 + 4)\n"
            "- Genel sorular (AI aktifse)\n"
            "- Sohbet\n\n"
            f"Aktif ajanlar: {agents}"
        )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        user_message = update.message.text

        # Kullaniciyi ve mesajini kaydet
        self.db.get_or_create_user(user.id, user.username)
        self.db.save_message(user.id, "user", user_message)

        # Konusma gecmisini al (LLM baglami icin)
        history = self.db.get_recent_history(user.id, limit=10)

        try:
            agent, answer = self.router.route(user_message, history=history)
            self.db.save_message(
                user.id, "assistant", answer, agent_name=agent.name,
            )
            await update.message.reply_text(answer)
        except Exception as exc:
            logger.exception("Mesaj islenirken hata: %s", exc)
            await update.message.reply_text(
                "Bir seyler ters gitti, ama duzeltmeye calisiyorum. "
                "Lutfen tekrar dener misin?"
            )

    def build_application(self) -> Application:
        app = Application.builder().token(self.config.telegram_token).build()
        app.add_handler(CommandHandler("start", self.start_command))
        app.add_handler(CommandHandler("help", self.help_command))
        app.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
        )
        return app


def main():
    config = Config.from_env()
    service = BotService(config)
    app = service.build_application()

    mode = "AI" if config.llm_enabled else "kural-tabanli"
    logger.info("Bot baslatiliyor (%s mod)...", mode)

    if config.use_webhook and config.webhook_url:
        # WEBHOOK modu: Telegram guncellemeleri Flask uzerinden gelir.
        logger.info("Webhook modu: %s", config.webhook_url)
        app.run_webhook(
            listen="0.0.0.0",
            port=config.webhook_port,
            webhook_url=f"{config.webhook_url}/webhook",
        )
    else:
        # POLLING modu: gelistirmede varsayilan.
        app.run_polling()


if __name__ == "__main__":
    main()

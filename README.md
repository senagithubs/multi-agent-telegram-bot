# Multi-Agent AI Telegram Bot

A production-oriented, multi-agent chatbot for Telegram built with Python.
A central **router** inspects each incoming message, scores every agent's
confidence, and dispatches to the best-matching agent. Conversations are
persisted to a database and used as context for the LLM agent, so the bot
has memory.

Built to be extended: adding a new capability means writing one small agent
class — no changes to the router or core.

## Highlights

- **Multi-agent orchestration** — a router scores agents (0.0–1.0) and
  dispatches each message to the most suitable one.
- **Real LLM integration** — an OpenAI-powered agent with conversation
  memory. Falls back to rule-based agents automatically if no API key is
  configured (graceful degradation).
- **Persistent memory** — users and message history stored via SQLAlchemy
  ORM (SQLite in dev, PostgreSQL in production via `DATABASE_URL`).
- **Flask webhook support** — run via long-polling in development or via a
  Flask webhook server in production, with a `/health` endpoint for deploys.
- **Safe math agent** — arithmetic parsed with `ast`, never `eval()`, so
  there is no code-injection risk.
- **Robust error handling** — a failing agent never crashes the bot; errors
  are logged and the user gets a friendly reply.
- **Automated tests** — router, agents and database covered by `pytest`.

## Architecture

```
                 Telegram
                    │
        ┌───────────┴───────────┐
        │  polling  OR  webhook │   (Flask: /webhook, /health)
        └───────────┬───────────┘
                    ▼
                 bot.py  (BotService)
                    │
        ┌───────────┼────────────┐
        ▼           ▼            ▼
   Database      Router      (history as LLM context)
   (SQLAlchemy)    │
                   ├──► MathAgent   (safe arithmetic, ast)
                   ├──► LLMAgent    (OpenAI + memory)
                   └──► EchoAgent   (rule-based fallback)
```

The router asks every agent `can_handle(message) -> float` and dispatches
to the highest scorer. Specialist agents (math) outrank the general LLM
agent, which outranks the fallback. Adding an agent is O(1): implement the
interface, add it to the list.

## Tech stack

Python · python-telegram-bot · OpenAI API · SQLAlchemy · Flask · pytest

## Project structure

```
multi_agent_bot/
├── bot.py                 # entry point, wires everything together
├── requirements.txt
├── .env.example
├── test_router.py         # automated tests (router + agents + db)
├── core/
│   ├── config.py          # env-based configuration
│   ├── database.py        # SQLAlchemy models + data access
│   └── web.py             # Flask webhook server + health check
└── agents/
    ├── base_agent.py      # abstract base class
    ├── router.py          # orchestration logic
    ├── math_agent.py      # safe arithmetic agent
    ├── llm_agent.py       # OpenAI agent with memory
    └── echo_agent.py      # rule-based fallback agent
```

## Setup

1. Create a bot with [@BotFather](https://t.me/BotFather) and copy the token.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure environment (copy the example and fill it in):
   ```bash
   cp .env.example .env
   # edit .env, then export the variables (or use a tool like direnv)
   export TELEGRAM_BOT_TOKEN="..."
   export OPENAI_API_KEY="..."   # optional
   ```
4. Run:
   ```bash
   python bot.py
   ```

## Running tests

```bash
pytest
```

## Development vs production

- **Development:** leave `USE_WEBHOOK=false`. The bot long-polls Telegram.
- **Production:** set `USE_WEBHOOK=true` and `WEBHOOK_URL` to your public
  HTTPS URL. Telegram pushes updates to the Flask `/webhook` endpoint; the
  `/health` endpoint lets your platform verify the service is up.

## Adding a new agent

```python
from agents.base_agent import BaseAgent

class WeatherAgent(BaseAgent):
    name = "weather"

    def can_handle(self, message: str) -> float:
        return 0.9 if "weather" in message.lower() else 0.0

    def handle(self, message: str) -> str:
        return "Sunny, 24°C."   # call a weather API here
```

Register it in `bot.py`'s router list — nothing else changes.

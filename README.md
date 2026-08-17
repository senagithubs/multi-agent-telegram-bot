# Multi-Agent Telegram Bot

A multi-agent Telegram chatbot where a router scores every agent's confidence in handling an incoming message and dispatches to the best match, with an LLM agent that has persistent conversation memory.

## What it does

- Routes every incoming Telegram message to the best-suited agent based on a confidence score, rather than hardcoded if/else logic.
- Runs a specialist MathAgent that safely evaluates arithmetic with Python's ast module (never eval()), so there is no code-injection risk.
- Runs an OpenAI-powered LLM agent for general questions, using the user's recent conversation history (persisted via SQLAlchemy) as context so replies stay coherent across turns.
- Falls back automatically to a rule-based agent when no OPENAI_API_KEY is configured, so the bot always responds even without an LLM.
- Serves updates either via long-polling for development or a Flask webhook with a /health endpoint for production deploys.
- Catches and logs agent failures so a broken agent never crashes the bot; the user gets a friendly error message instead.

## How confidence-based routing works

Every agent implements a can_handle(message) method that returns a confidence score between 0.0 and 1.0. On each incoming message, the Router (agents/router.py) asks all registered agents to score the message, then dispatches to whichever agent scored highest. The agents are registered in an order that reflects how specific they are: the math agent scores 0.95 when a message looks like a pure arithmetic expression, the LLM agent scores 0.5 whenever it is enabled - high enough to beat the fallback, low enough to lose to a specialist - and the fallback chat agent always scores a flat 0.1, so it only wins when nothing else can handle the message.

Because routing is just a score comparison, adding a new capability means writing one more agent class with its own can_handle logic - no changes to the router or to any other agent are needed.

## Tech stack

- Python
- python-telegram-bot
- OpenAI API, with a rule-based fallback when no key is set
- SQLAlchemy ORM (SQLite in development, PostgreSQL in production)
- Flask for the production webhook and /health endpoint
- pytest for router, agent and database tests

## Quickstart

```bash
pip install -r requirements.txt
cp .env.example .env
# edit .env, then export the variables (or use a tool like direnv)
export TELEGRAM_BOT_TOKEN="..."
export OPENAI_API_KEY="..."   # optional
python bot.py
```

Run the tests:

```bash
pytest
```

## Example

```
User: 12 * (3 + 4)
Router: -> math agent (score: 0.95)
Bot: Sonuc: 84

User: merhaba
Router: -> chat agent (score: 0.10)
Bot: Merhaba! Sana nasil yardimci olabilirim?
```

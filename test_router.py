"""
test_router.py
--------------
Otomatik testler (pytest ile calistirilir).
Router, ajanlar ve veritabani davranisini dogrular.
"""

from core import Database
from agents import MathAgent, EchoAgent, LLMAgent, Router


def make_router():
    # LLM anahtari olmadan: LLMAgent devre disi kalir, digerleri calisir
    return Router(agents=[MathAgent(), LLMAgent(api_key=None), EchoAgent()])


# --- Router / ajan testleri ---------------------------------------------

def test_math_is_routed_to_math_agent():
    agent, answer = make_router().route("2 + 2")
    assert agent.name == "math"
    assert "4" in answer


def test_complex_math_expression():
    _, answer = make_router().route("12 * (3 + 4)")
    assert "84" in answer


def test_division_by_zero_is_handled():
    _, answer = make_router().route("5 / 0")
    assert "sifir" in answer.lower() or "sıfır" in answer.lower() or "0" in answer


def test_greeting_goes_to_chat_agent():
    agent, _ = make_router().route("merhaba")
    assert agent.name == "chat"


def test_unknown_message_falls_back_to_chat_when_no_llm():
    # LLM kapaliyken bilinmeyen mesaj chat (fallback) ajanina gider
    agent, _ = make_router().route("bugun hava nasil")
    assert agent.name == "chat"


def test_empty_agent_list_raises():
    import pytest
    with pytest.raises(ValueError):
        Router(agents=[])


def test_llm_agent_disabled_without_key():
    agent = LLMAgent(api_key=None)
    assert agent.enabled is False
    assert agent.can_handle("herhangi bir sey") == 0.0


# --- Veritabani testleri -------------------------------------------------

def test_database_saves_and_retrieves_history():
    db = Database("sqlite:///:memory:")
    db.save_message(999, "user", "merhaba")
    db.save_message(999, "assistant", "selam", agent_name="chat")
    history = db.get_recent_history(999)
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[1]["content"] == "selam"


def test_database_get_or_create_user_is_idempotent():
    db = Database("sqlite:///:memory:")
    u1 = db.get_or_create_user(555, "ali")
    u2 = db.get_or_create_user(555, "ali")
    # Ayni telegram_id icin ayni kullanici donmeli, kopya olusmamali
    assert u1.telegram_id == u2.telegram_id


def test_history_respects_limit():
    db = Database("sqlite:///:memory:")
    for i in range(20):
        db.save_message(777, "user", f"mesaj {i}")
    history = db.get_recent_history(777, limit=5)
    assert len(history) == 5



import inspect
import logging

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class Router:
    def __init__(self, agents: list[BaseAgent]):
        if not agents:
            raise ValueError("En az bir ajan gerekli.")
        self.agents = agents

    def route(
        self, message: str, history: list[dict] | None = None,
    ) -> tuple[BaseAgent, str]:
        """Mesajı en uygun ajana yönlendirir.

        history: opsiyonel konuşma geçmişi. Sadece bunu destekleyen
        ajanlara (örn. LLMAgent) iletilir.
        """
        scored = [(agent, agent.can_handle(message)) for agent in self.agents]
        best_agent, best_score = max(scored, key=lambda pair: pair[1])

        logger.info(
            "Router: '%s' -> %s ajani (puan: %.2f)",
            message, best_agent.name, best_score,
        )

        # Ajanin handle() metodu 'history' parametresi kabul ediyor mu?
        sig = inspect.signature(best_agent.handle)
        if "history" in sig.parameters:
            answer = best_agent.handle(message, history=history)
        else:
            answer = best_agent.handle(message)

        return best_agent, answer

    def list_agents(self) -> list[str]:
        return [agent.name for agent in self.agents]

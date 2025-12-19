from __future__ import annotations

class AIProvider:
    """
    Provider simples para MVP.
    Pode ser substituído por OpenAI, local LLM, etc.
    """

    def explain(self, prompt: str) -> str:
        # MVP: placeholder explicito
        return (
            "AI provider not configured yet.\n\n"
            "Prompt received:\n"
            "----------------\n"
            f"{prompt}"
        )

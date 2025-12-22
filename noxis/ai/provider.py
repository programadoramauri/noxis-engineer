from __future__ import annotations


class AIProvider:
    """
    Provider simples para MVP.
    Pode ser substituído por OpenAI, local LLM, etc.
    """

    def explain(self, prompt: str) -> str:
        # MVP: placeholder explicito
        return f"AI provider not configured yet.\n\nPrompt received:\n----------------\n{prompt}"

    def generate_tests(self, prompt: str) -> dict[str, str]:
        """
        Returns {filename: content}
        """

        response = self._call_model(prompt)
        import json

        return json.loads(response)

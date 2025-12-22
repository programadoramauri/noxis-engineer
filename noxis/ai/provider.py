from __future__ import annotations
from pathlib import Path
import json
import re
import urllib.request
from dataclasses import dataclass
from typing import Any
import yaml


@dataclass(frozen=True)
class LocalHTTPConfig:
    base_url: str
    endpoint: str
    model: str
    timeout_seconds: int = 120


class AIProvider:
    """
    MVP: Provider local via HTTP (sem dependências externas).
    - Mantém fallback determinístico para não quebrar o fluxo
    """

    def __init__(self, config: LocalHTTPConfig | None = None) -> None:
        self.config = config or self._load_local_http_config()

    def explain(self, prompt: str) -> str:
        # MVP: pode usar o mesmo backend local no futuro.
        # Por enquanto, mantém o comportamento simples.
        return (
            "Local provider configured.\n\n"
            "Explain is not implemented with the model yet.\n\n"
            "Prompt received:\n"
            "----------------\n"
            "f{prompt}"
        )

    def generate_tests(self, prompt: str) -> dict[str, str]:
        """
        Returns {filename: content}
        """

        try:
            raw = self._call_local_model(prompt)
            payload = self._parse_json_mapping(raw)
            self._validate_tests_mapping(payload)
            return payload
        except Exception:
            return self._fallback_tests()

    def _call_local_model(self, prompt: str) -> str:
        cfg = self.config
        url = cfg.base_url.rstrip("/") + cfg.endpoint

        # Payload genérico: funciona bem com vários servidores locais.
        # Ajuste depois conforme seu servidos (ex.: "stream": false etc.).
        request_payload: dict[str, Any] = {
            "model": cfg.model,
            "prompt": prompt,
            "stream": False,
        }

        req = urllib.request.Request(
            url=url,
            data=json.dumps(request_payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=cfg.timeout_seconds) as resp:
            body = resp.read().decode("utf-8", errors="replace")

        # Muitos servidores retornam JSON com campo "response" ou "text"
        # mas alguns retornam direto texto. Vamos tratar ambos.

        try:
            as_json = json.loads(body)
            if isinstance(as_json, dict):
                # chaves comuns
                for key in ("response", "text", "output", "message", "content"):
                    v = as_json.get(key)
                    if isinstance(v, str) and v.strip():
                        return v
                choices = as_json.get("choices")
                if isinstance(choices, list) and choices:
                    first = choices[0]
                    if isinstance(first, dict):
                        v = first.get("text") or first.get("message") or first.get("content")
                        if isinstance(v, str) and v.strip():
                            return v
            return body
        except Exception:
            return body

    def _parse_json_mapping(self, raw: str) -> dict[str, str]:
        """
        Espera um JSON objeto: {"test_x.py": "...", ...}
        Se vier texto com JSON "embutido", extrai o primeiro bloco JSON.
        """
        raw = raw.strip()

        # 1) se já for JSON puro
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                return {str(k): str(v) for k, v in parsed.items()}
        except Exception:
            pass

        # 2) extrair bloco JSON dentro do texto (inclusive em ```json ... ```)
        candidate = self._extract_first_json_object(raw)
        parsed = json.loads(candidate)
        if not isinstance(parsed, dict):
            raise ValueError("Model output JSON is not an object mapping filename->content")
        return {str(k): str(v) for k, v in parsed.items()}

    def _extract_first_json_object(self, text: str) -> str:
        # tenta pegar dentro de ```json ... ```
        fence = re.search(r"```(?:json)?\s*({.*?})\s*```", text, flags=re.DOTALL)
        if fence:
            return fence.group(1)

        start = text.find("{")
        if start == -1:
            raise ValueError("No JSON object found in model output")

        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    return text[start : i + 1]
        raise ValueError("Unbalanced JSON braces in model output")

    def _validate_tests_mapping(self, mapping: dict[str, str]) -> None:
        if not mapping:
            raise ValueError("Empty tests mapping")
        for filename, content in mapping.items():
            if not filename.endswith(".py"):
                raise ValueError(f"Invalid test filename (must end with .py): {filename}")
            if "/" in filename or "\\" in filename:
                # MVP: impede path traversal; tudo vai para tests/
                raise ValueError(f"Invalid filename (no paths allowed): {filename}")
            if len(content.strip()) < 10:
                raise ValueError(f"Test file content too short: {filename}")

    def _call_model(self, prompt: str) -> str:
        """
        MVP stub for AI calls.
        Returns a deterministic JSON with a simple pytest test.
        """
        return """
            {
                "test_smoke.py": "def test_smoke():\\n  assert True"
            }
            """

    def _load_local_http_config(self) -> LocalHTTPConfig:
        # 1) tentar .noxis/policies.yml
        policies_path = Path(".noxis/policies.yml")
        if policies_path.exists():
            data = yaml.safe_load(policies_path.read_text(encoding="utf-8"))
        else:
            # 2) fallback: defaults.yml do pacote
            from noxis.policies.loader import load_default_policies_yaml

            data = yaml.safe_load(load_default_policies_yaml())

        ai_cfg = (data or {}).get("ai", {})
        local = ai_cfg.get("local_http", {})

        base_url = local.get("base_url", "http://127.0.0.1:11434")
        endpoint = local.get("endpoint", "/api/generate")
        model = local.get("model", "qwen2.5-coder:7b")
        timeout = int(local.get("timeout_seconds", 120))

        return LocalHTTPConfig(
            base_url=base_url, endpoint=endpoint, model=model, timeout_seconds=timeout
        )

    def _fallback_tests(self) -> dict[str, str]:
        return {"test_smoke.py": "def test_smoke():\n   assert True\n"}

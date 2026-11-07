"""Client LLM universel — OpenRouter (défaut) ou Anthropic selon la clé disponible."""
from __future__ import annotations

import requests

from ..config import LLM_MODEL, LLM_URL, get_secret


class LLMError(RuntimeError):
    pass


class LLMClient:
    def __init__(self, api_key: str | None = None, model: str | None = None, timeout: int = 60):
        # OpenRouter en priorité, puis Anthropic en fallback
        self.api_key   = api_key or get_secret("OPENROUTER_API_KEY") or get_secret("ANTHROPIC_API_KEY")
        self._provider = "openrouter" if get_secret("OPENROUTER_API_KEY") else "anthropic"
        self.model     = model or LLM_MODEL
        self.timeout   = timeout

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def complete(self, user: str, system: str = "", max_tokens: int = 1800, temperature: float = 0.3) -> str:
        if not self.available:
            raise LLMError("Aucune clé API configurée (OPENROUTER_API_KEY ou ANTHROPIC_API_KEY).")

        if self._provider == "openrouter":
            return self._openrouter(user, system, max_tokens, temperature)
        return self._anthropic(user, system, max_tokens, temperature)

    # ── OpenRouter (format OpenAI) ────────────────────────────────────────────
    def _openrouter(self, user: str, system: str, max_tokens: int, temperature: float) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": user})

        try:
            r = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                json={
                    "model": self.model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                },
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://ntic-radar.local",
                    "X-Title": "Ntic Radar CV Agent",
                },
                timeout=self.timeout,
            )
        except requests.RequestException as e:
            raise LLMError(f"Erreur réseau : {str(e)[:120]}") from e

        if r.status_code != 200:
            raise LLMError(f"OpenRouter {r.status_code} : {r.text[:200]}")

        try:
            return r.json()["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError) as e:
            raise LLMError(f"Réponse inattendue : {r.text[:200]}") from e

    # ── Anthropic (format natif) ──────────────────────────────────────────────
    def _anthropic(self, user: str, system: str, max_tokens: int, temperature: float) -> str:
        body = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": user}],
        }
        if system:
            body["system"] = system

        try:
            r = requests.post(
                "https://api.anthropic.com/v1/messages",
                json=body,
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                timeout=self.timeout,
            )
        except requests.RequestException as e:
            raise LLMError(f"Erreur réseau : {str(e)[:120]}") from e

        if r.status_code != 200:
            raise LLMError(f"Anthropic {r.status_code} : {r.text[:200]}")

        blocs = r.json().get("content", [])
        return "".join(b.get("text", "") for b in blocs if b.get("type") == "text").strip()


def get_client() -> LLMClient:
    return LLMClient()

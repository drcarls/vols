"""LLM provider with a strict remit and a persistent cache.

The LLM is used only where it has comparative advantage over code:

    * semantic classification of a name into an industry/category
    * qualitative brandability commentary
    * reasoning about whether a specific company plausibly wants a specific name
    * writing the prose explanation of a ranking

It is never used for arithmetic, parsing, database logic, comparable-sale
selection, or any scoring rule that can be written down. Those all live in
``app/scoring`` as ordinary deterministic code, precisely so that a ranking can
be audited rather than believed.

Every call demands structured JSON, is content-addressed and cached in SQLite,
and is capped per run. The default provider is ``NullLlmProvider``: with no API
key the pipeline runs end to end using the deterministic classifier, and the
affected fields are marked MISSING rather than guessed.
"""

from __future__ import annotations

import hashlib
import json
import logging
from abc import ABC, abstractmethod
from typing import Any

from app.config import get_settings

log = logging.getLogger(__name__)


class LlmUnavailable(RuntimeError):
    pass


class LlmProvider(ABC):
    name = "llm"

    @property
    @abstractmethod
    def available(self) -> bool: ...

    @abstractmethod
    def complete_json(self, task: str, prompt: str, schema_hint: str,
                      max_tokens: int = 1024) -> dict[str, Any]:
        """Return a parsed JSON object, or raise ``LlmUnavailable``."""

    def describe(self) -> dict[str, Any]:
        return {"name": self.name, "available": self.available}


class NullLlmProvider(LlmProvider):
    """No LLM configured. Callers fall back to deterministic logic."""

    name = "llm.null"

    @property
    def available(self) -> bool:
        return False

    def complete_json(self, task, prompt, schema_hint, max_tokens=1024):
        raise LlmUnavailable("no LLM provider configured (set LLM_PROVIDER=anthropic)")


class CachedLlmProvider(LlmProvider):
    """Wraps a provider with a SQLite-backed, content-addressed cache.

    The cache key covers model + task + prompt, so a prompt edit is a cache
    miss and an unchanged prompt is free. This is what keeps a 10,000-domain
    run affordable and makes reruns reproducible.
    """

    def __init__(self, inner: LlmProvider, *, enabled: bool = True,
                 max_calls: int = 200) -> None:
        self.inner = inner
        self.enabled = enabled
        self.max_calls = max_calls
        self.calls_made = 0
        self.cache_hits = 0
        self.name = f"cached({inner.name})"

    @property
    def available(self) -> bool:
        return self.inner.available

    @staticmethod
    def _key(model: str, task: str, prompt: str) -> str:
        return hashlib.sha256(f"{model}\x00{task}\x00{prompt}".encode()).hexdigest()

    def complete_json(self, task, prompt, schema_hint, max_tokens=1024):
        if not self.inner.available:
            raise LlmUnavailable("no LLM provider configured")

        from app.db.base import session_scope
        from app.models.analysis import LlmCacheEntry

        model = getattr(self.inner, "model", "unknown")
        key = self._key(model, task, prompt + schema_hint)

        if self.enabled:
            with session_scope() as s:
                hit = s.query(LlmCacheEntry).filter_by(cache_key=key).one_or_none()
                if hit is not None:
                    self.cache_hits += 1
                    return dict(hit.response_json)

        if self.calls_made >= self.max_calls:
            raise LlmUnavailable(
                f"LLM call budget exhausted for this run ({self.max_calls})")

        result = self.inner.complete_json(task, prompt, schema_hint, max_tokens)
        self.calls_made += 1

        if self.enabled:
            with session_scope() as s:
                s.merge(LlmCacheEntry(cache_key=key, model=model, task=task,
                                      prompt=prompt, response_json=result))
        return result

    def describe(self) -> dict[str, Any]:
        return {"name": self.name, "available": self.available,
                "calls_made": self.calls_made, "cache_hits": self.cache_hits,
                "max_calls": self.max_calls}


class AnthropicLlmProvider(LlmProvider):
    """Anthropic Messages API. Requires ``ANTHROPIC_API_KEY``.

    Uses a tool-call to force valid JSON rather than parsing prose, so a
    malformed response is a hard error instead of a silently wrong field.
    """

    name = "llm.anthropic"

    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model
        self._client = None

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def _get_client(self):
        if self._client is None:
            try:
                import anthropic
            except ImportError as exc:  # pragma: no cover - optional dependency
                raise LlmUnavailable(
                    "anthropic package not installed; pip install anthropic") from exc
            self._client = anthropic.Anthropic(api_key=self.api_key)
        return self._client

    def complete_json(self, task, prompt, schema_hint, max_tokens=1024):
        client = self._get_client()
        tool = {
            "name": "emit_result",
            "description": f"Return the structured result for task: {task}",
            "input_schema": json.loads(schema_hint),
        }
        try:
            resp = client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                tools=[tool],
                tool_choice={"type": "tool", "name": "emit_result"},
                messages=[{"role": "user", "content": prompt}],
            )
        except Exception as exc:  # noqa: BLE001 - surface as unavailability
            raise LlmUnavailable(f"LLM call failed: {exc}") from exc

        for block in resp.content:
            if getattr(block, "type", None) == "tool_use":
                return dict(block.input)
        raise LlmUnavailable("LLM returned no structured output")


def build_llm_provider() -> LlmProvider:
    s = get_settings()
    if s.llm_provider == "anthropic" and s.anthropic_api_key:
        inner: LlmProvider = AnthropicLlmProvider(s.anthropic_api_key, s.llm_model)
    else:
        inner = NullLlmProvider()
    return CachedLlmProvider(inner, enabled=s.llm_cache_enabled,
                             max_calls=s.llm_max_calls_per_run)

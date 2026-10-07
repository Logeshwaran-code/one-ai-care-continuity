"""Provider-agnostic LLM gateway: versioned prompt files, JSON-schema (pydantic) validation,
caching, retries, timeouts and cost/latency logging. Default provider is an offline deterministic
rule-based 'mock' so the platform runs with no API key; switch with LLM_PROVIDER=openai_compat
(works with OpenAI, vLLM, Ollama, LM Studio, etc.)."""
import asyncio
import hashlib
import json
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from string import Template
from typing import Any, Protocol, TypeVar

import httpx
from prometheus_client import Counter, Histogram
from pydantic import BaseModel, ValidationError

from app.config import settings

log = logging.getLogger("llm")
PROMPT_DIR = Path(__file__).parent / "prompts"
LLM_LATENCY = Histogram("llm_latency_seconds", "LLM call latency", ["provider", "task"])
LLM_CALLS = Counter("llm_calls_total", "LLM calls", ["provider", "task", "outcome"])
T = TypeVar("T", bound=BaseModel)


@dataclass(frozen=True)
class LLMRequest:
    task: str
    prompt: str
    variables: dict[str, Any]


class Provider(Protocol):
    name: str

    async def complete(self, req: LLMRequest) -> str: ...


# --- deterministic offline handlers ------------------------------------------------------------
PLAIN = {  # tiny seed glossary (English); production should use an LLM or a curated glossary
    "hypertension": "high blood pressure", "hyperglycemia": "high blood sugar", "hypoglycemia": "low blood sugar",
    "antihypertensive": "blood pressure medicine", "renal": "kidney", "hepatic": "liver", "cardiac": "heart",
    "myocardial infarction": "heart attack", "edema": "swelling", "dyspnea": "shortness of breath",
    "prn": "only when needed", "bid": "twice a day", "od": "once a day", "tid": "three times a day",
    "hba1c": "average blood sugar over about 3 months (HbA1c)", "lipid": "blood fat", "analgesic": "pain reliever",
    "contraindicated": "not safe to use together or in some people", "adverse": "unwanted", "bilateral": "on both sides",
}
UI_PHRASES = {  # fixed, human-reviewable phrases; free-text translation needs a real LLM provider
    "Take your medicines as your doctor told you.": {"ta": "உங்கள் மருத்துவர் சொன்னபடி மருந்துகளை எடுத்துக்கொள்ளுங்கள்.", "hi": "अपने डॉक्टर के बताए अनुसार दवाइयाँ लें।"},
    "Please talk to your doctor.": {"ta": "தயவுசெய்து உங்கள் மருத்துவரிடம் பேசுங்கள்.", "hi": "कृपया अपने डॉक्टर से बात करें।"},
}


def _mock_simplify(v: dict[str, Any]) -> str:
    text = str(v.get("text", ""))
    level = str(v.get("level", "simple"))
    for term, plain in sorted(PLAIN.items(), key=lambda kv: -len(kv[0])):
        text = _replace_word(text, term, plain)
    sentences = [s.strip() for s in text.replace("\n", " ").split(".") if s.strip()]
    if level == "very_simple":
        sentences = [s if len(s.split()) <= 14 else " ".join(s.split()[:14]) + " ..." for s in sentences]
    return "Your report says: " + ". ".join(sentences) + ("." if sentences else "")


def _replace_word(text: str, term: str, repl: str) -> str:
    import re

    return re.sub(rf"\b{re.escape(term)}\b", repl, text, flags=re.IGNORECASE)


def _mock_translate(v: dict[str, Any]) -> str:
    text, target = str(v.get("text", "")), str(v.get("target", "en"))
    if target == "en":
        return text
    hit = UI_PHRASES.get(text.strip())
    return hit[target] if hit and target in hit else text


def _mock_narrative(v: dict[str, Any]) -> str:
    return str(v.get("facts", ""))


MOCK_HANDLERS: dict[str, Callable[[dict[str, Any]], str]] = {
    "simplify": _mock_simplify, "translate": _mock_translate, "visit_narrative": _mock_narrative,
}


class MockProvider:
    name = "mock"

    async def complete(self, req: LLMRequest) -> str:
        handler = MOCK_HANDLERS.get(req.task)
        if handler is None:
            raise ValueError(f"mock provider has no handler for task {req.task}")
        return handler(req.variables)


class OpenAICompatProvider:
    name = "openai_compat"

    async def complete(self, req: LLMRequest) -> str:
        headers = {"Authorization": f"Bearer {settings.llm_api_key}"} if settings.llm_api_key else {}
        body = {"model": settings.llm_model, "temperature": 0.1,
                "messages": [{"role": "user", "content": req.prompt}]}
        async with httpx.AsyncClient(timeout=settings.llm_timeout_s) as client:
            r = await client.post(settings.llm_base_url.rstrip("/") + "/chat/completions", json=body, headers=headers)
            r.raise_for_status()
            return str(r.json()["choices"][0]["message"]["content"])


def load_prompt(task: str, version: str = "v1") -> tuple[Template, str]:
    path = PROMPT_DIR / f"{task}.{version}.txt"
    return Template(path.read_text(encoding="utf-8")), f"{task}.{version}"


class _Cache:
    def __init__(self) -> None:
        self._d: dict[str, tuple[float, str]] = {}

    def get(self, k: str) -> str | None:
        hit = self._d.get(k)
        if hit and hit[0] > time.monotonic():
            return hit[1]
        return None

    def set(self, k: str, v: str) -> None:
        if len(self._d) > 2000:
            self._d.clear()
        self._d[k] = (time.monotonic() + settings.llm_cache_ttl_s, v)


class LLMGateway:
    def __init__(self, provider: Provider | None = None) -> None:
        self.provider = provider or (OpenAICompatProvider() if settings.llm_provider == "openai_compat" else MockProvider())
        self.cache = _Cache()

    async def generate(self, task: str, variables: dict[str, Any], schema: type[T] | None = None) -> str | T:
        tpl, prompt_id = load_prompt(task)
        prompt = tpl.safe_substitute({k: str(v) for k, v in variables.items()})
        key = hashlib.sha256(f"{self.provider.name}|{prompt_id}|{prompt}".encode()).hexdigest()
        raw = self.cache.get(key)
        if raw is None:
            raw = await self._call(LLMRequest(task, prompt, variables))
            self.cache.set(key, raw)
        if schema is None:
            return raw
        try:
            return schema.model_validate(json.loads(raw))
        except (ValidationError, json.JSONDecodeError) as exc:
            LLM_CALLS.labels(self.provider.name, task, "schema_invalid").inc()
            raise ValueError("LLM output failed JSON-schema validation") from exc

    async def _call(self, req: LLMRequest) -> str:
        last: Exception | None = None
        for attempt in range(settings.llm_retries + 1):
            start = time.perf_counter()
            try:
                out = await asyncio.wait_for(self.provider.complete(req), timeout=settings.llm_timeout_s)
                dt = time.perf_counter() - start
                LLM_LATENCY.labels(self.provider.name, req.task).observe(dt)
                LLM_CALLS.labels(self.provider.name, req.task, "ok").inc()
                log.info("llm_call", extra={"task": req.task, "provider": self.provider.name, "latency_ms": round(dt * 1000),
                                            "approx_tokens": (len(req.prompt) + len(out)) // 4, "attempt": attempt})
                return out
            except Exception as exc:  # noqa: BLE001 - retry any provider failure
                last = exc
                LLM_CALLS.labels(self.provider.name, req.task, "error").inc()
                await asyncio.sleep(min(0.2 * 2**attempt, 2))
        raise RuntimeError(f"LLM call failed after retries: {last}")


gateway = LLMGateway()

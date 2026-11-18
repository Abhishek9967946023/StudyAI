"""Server-side adapters for configurable generative AI providers."""

import json
import logging
import time
import urllib.error
import urllib.parse
import urllib.request
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Optional, Tuple

from django.conf import settings

from .ollama_service import check_ollama_status, query_ollama

logger = logging.getLogger(__name__)


_PROVIDER_ALIASES = {
    "openai-compatible": "openai_compatible",
    "openai_compatible": "openai_compatible",
    "compatible": "openai_compatible",
}


def _normalize_provider(provider: Optional[str]) -> str:
    value = str(provider or "").strip().lower()
    return _PROVIDER_ALIASES.get(value, value)


def _provider_config(provider: str) -> Tuple[str, str, str]:
    if provider in ("openai", "openai_compatible"):
        return (
            getattr(settings, "OPENAI_API_KEY", ""),
            getattr(settings, "OPENAI_MODEL", "gpt-4o-mini"),
            getattr(settings, "OPENAI_BASE_URL", "https://api.openai.com/v1"),
        )
    if provider == "gemini":
        return (
            getattr(settings, "GEMINI_API_KEY", ""),
            getattr(settings, "GEMINI_MODEL", "gemini-2.0-flash"),
            getattr(settings, "GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta"),
        )
    if provider == "anthropic":
        return (
            getattr(settings, "ANTHROPIC_API_KEY", ""),
            getattr(settings, "ANTHROPIC_MODEL", "claude-3-5-haiku-latest"),
            getattr(settings, "ANTHROPIC_BASE_URL", "https://api.anthropic.com/v1"),
        )
    return "", "", ""


def _provider_is_configured(provider: str) -> bool:
    provider = _normalize_provider(provider)
    if provider == "ollama":
        return bool(check_ollama_status().get("is_online"))
    if provider in ("openai", "openai_compatible", "gemini", "anthropic"):
        api_key, _, base_url = _provider_config(provider)
        if provider == "openai_compatible":
            return bool(api_key) or base_url.rstrip("/") != "https://api.openai.com/v1"
        return bool(api_key)
    return False


def check_ai_provider_status() -> Dict[str, Any]:
    """Report provider configuration without claiming that a remote API is reachable."""
    provider = _normalize_provider(getattr(settings, "AI_PROVIDER", "ollama"))
    if provider == "ollama":
        status = check_ollama_status()
        return {
            **status,
            "provider": provider,
            "can_generate": bool(status.get("is_online")),
            "is_configured": True,
        }

    _, model, _ = _provider_config(provider)
    configured = _provider_is_configured(provider)
    fallback = _normalize_provider(getattr(settings, "AI_FALLBACK_PROVIDER", ""))
    fallback_configured = bool(fallback and fallback != provider and _provider_is_configured(fallback))
    can_generate = configured or fallback_configured
    if provider not in ("openai", "openai_compatible", "gemini", "anthropic"):
        message = f"Unsupported AI provider '{provider}'."
    elif configured:
        message = f"{provider} credentials are configured; availability is checked for each request."
    elif fallback_configured:
        message = f"{provider} is not configured; the configured {fallback} fallback may be used."
    else:
        message = f"Credentials for {provider} are not configured."

    return {
        "provider": provider,
        "default_model": model,
        "models": [],
        "is_online": False,
        "is_configured": configured,
        "can_generate": can_generate,
        "message": message,
    }


def _target_model(provider: str, requested_model: Optional[str]) -> str:
    _, configured_model, _ = _provider_config(provider)
    if requested_model and requested_model != "llama3:latest":
        return requested_model
    return configured_model


def _decode_content(content: Any) -> Optional[str]:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        text_parts = [
            part.get("text", "")
            for part in content
            if isinstance(part, dict) and isinstance(part.get("text"), str)
        ]
        return "\n".join(part for part in text_parts if part)
    return None


def _token_count(value: Any) -> Optional[int]:
    if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
        return value
    return None


def _extract_usage(provider: str, response_data: Dict[str, Any]) -> Dict[str, Optional[int]]:
    if provider in ("openai", "openai_compatible"):
        usage = response_data.get("usage", {})
        return {
            "prompt_tokens": _token_count(usage.get("prompt_tokens")),
            "completion_tokens": _token_count(usage.get("completion_tokens")),
        }
    if provider == "gemini":
        usage = response_data.get("usageMetadata", {})
        return {
            "prompt_tokens": _token_count(usage.get("promptTokenCount")),
            "completion_tokens": _token_count(usage.get("candidatesTokenCount")),
        }
    if provider == "anthropic":
        usage = response_data.get("usage", {})
        return {
            "prompt_tokens": _token_count(usage.get("input_tokens")),
            "completion_tokens": _token_count(usage.get("output_tokens")),
        }
    return {"prompt_tokens": None, "completion_tokens": None}


def _request_provider(
    provider: str,
    prompt: str,
    model: Optional[str],
    format_json: bool,
    temperature: Optional[float],
    timeout: Optional[int],
    max_tokens: Optional[int],
) -> Tuple[Optional[str], bool, Optional[str], Dict[str, Optional[int]]]:
    api_key, _, base_url = _provider_config(provider)
    if not api_key and provider != "openai_compatible":
        return None, False, f"Credentials for {provider} are not configured.", {}
    if (
        not api_key
        and provider == "openai_compatible"
        and base_url.rstrip("/") == "https://api.openai.com/v1"
    ):
        return None, False, "OPENAI_API_KEY is required for the default OpenAI endpoint.", {}

    target_model = _target_model(provider, model)
    temp = temperature if temperature is not None else getattr(settings, "OLLAMA_TEMPERATURE", 0.2)
    request_timeout = timeout if timeout is not None else getattr(settings, "OLLAMA_TIMEOUT", 120)
    token_limit = max_tokens or getattr(settings, "AI_MAX_TOKENS", 3000)
    headers = {"Content-Type": "application/json", "User-Agent": "StudyAI-Backend"}

    if provider in ("openai", "openai_compatible"):
        endpoint = base_url.rstrip("/")
        if not endpoint.endswith("/chat/completions"):
            endpoint += "/chat/completions"
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        payload: Dict[str, Any] = {
            "model": target_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temp,
            "max_tokens": token_limit,
        }
        if format_json:
            payload["response_format"] = {"type": "json_object"}
    elif provider == "gemini":
        endpoint = f"{base_url.rstrip('/')}/models/{urllib.parse.quote(target_model)}:generateContent"
        headers["x-goog-api-key"] = api_key
        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": temp, "maxOutputTokens": token_limit},
        }
        if format_json:
            payload["generationConfig"]["responseMimeType"] = "application/json"
    elif provider == "anthropic":
        endpoint = f"{base_url.rstrip('/')}/messages"
        headers["x-api-key"] = api_key
        headers["anthropic-version"] = "2023-06-01"
        payload = {
            "model": target_model,
            "max_tokens": token_limit,
            "temperature": temp,
            "messages": [{"role": "user", "content": prompt}],
        }
        if format_json:
            payload["system"] = "Return only a valid JSON object."
    else:
        return None, False, f"Unsupported AI provider '{provider}'.", {}

    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=request_timeout) as response:
            response_data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        return None, False, f"{provider} API returned HTTP {error.code}.", {}
    except urllib.error.URLError as error:
        reason = str(error.reason)
        return None, False, f"{provider} API request failed: {reason[:200]}", {}
    except (TimeoutError, json.JSONDecodeError, UnicodeDecodeError):
        return None, False, f"{provider} returned an invalid or timed-out response.", {}

    try:
        if provider in ("openai", "openai_compatible"):
            content = response_data["choices"][0]["message"]["content"]
        elif provider == "gemini":
            content = response_data["candidates"][0]["content"]["parts"]
        else:
            content = response_data["content"]
        text = _decode_content(content)
    except (KeyError, IndexError, TypeError):
        return None, False, f"{provider} returned an unexpected response shape.", {}

    if not text:
        return None, False, f"{provider} returned no text.", {}
    return text, True, None, _extract_usage(provider, response_data)


def _query_provider(
    provider: str,
    prompt: str,
    model: Optional[str],
    format_json: bool,
    temperature: Optional[float],
    timeout: Optional[int],
    num_predict: Optional[int],
    num_ctx: Optional[int],
) -> Tuple[Optional[str], bool, Optional[str], Dict[str, Optional[int]]]:
    if provider == "ollama":
        result = query_ollama(
            prompt,
            model=model,
            format_json=format_json,
            temperature=temperature,
            timeout=timeout,
            num_predict=num_predict,
            num_ctx=num_ctx,
            include_usage=True,
        )
        if len(result) == 4:
            return result
        text, success, error = result
        return text, success, error, {}
    return _request_provider(
        provider,
        prompt,
        model,
        format_json,
        temperature,
        timeout,
        num_predict,
    )


def _failure_code(error: Optional[str]) -> str:
    message = str(error or "").lower()
    if "credential" in message or "required" in message:
        return "provider_not_configured"
    if "http " in message:
        return "provider_http_error"
    if "timeout" in message or "timed out" in message:
        return "provider_timeout"
    if "unexpected response shape" in message or "invalid response" in message:
        return "invalid_provider_response"
    if "returned no text" in message:
        return "empty_provider_response"
    return "provider_request_failed"


def _estimate_cost(model: str, usage: Dict[str, Optional[int]]) -> Optional[Decimal]:
    rates_by_model = getattr(settings, "AI_MODEL_PRICING_USD_PER_1M", {})
    rates = rates_by_model.get(model) if isinstance(rates_by_model, dict) else None
    prompt_tokens = usage.get("prompt_tokens")
    completion_tokens = usage.get("completion_tokens")
    if not isinstance(rates, dict) or prompt_tokens is None or completion_tokens is None:
        return None

    try:
        input_rate = Decimal(str(rates["input"]))
        output_rate = Decimal(str(rates["output"]))
        if input_rate < 0 or output_rate < 0:
            return None
        cost = (
            Decimal(prompt_tokens) * input_rate
            + Decimal(completion_tokens) * output_rate
        ) / Decimal(1_000_000)
        return cost.quantize(Decimal("0.0000000001"))
    except (KeyError, InvalidOperation, TypeError, ValueError):
        return None


def _record_usage_event(
    provider: str,
    model: str,
    latency_ms: int,
    result: Tuple[Optional[str], bool, Optional[str], Dict[str, Optional[int]]],
    fallback_used: bool,
) -> None:
    _, success, error, usage = result
    try:
        from .models import AIUsageEvent

        AIUsageEvent.objects.create(
            provider=provider,
            model=model or "",
            prompt_tokens=usage.get("prompt_tokens"),
            completion_tokens=usage.get("completion_tokens"),
            latency_ms=max(0, latency_ms),
            success=success,
            fallback_used=fallback_used,
            failure_code="" if success else _failure_code(error),
            estimated_cost_usd=_estimate_cost(model, usage) if success else None,
        )
    except Exception:
        logger.exception("Could not persist AI provider usage metadata.")


def _effective_model(provider: str, requested_model: Optional[str]) -> str:
    if provider == "ollama":
        from .ollama_service import get_configured_model

        return requested_model or get_configured_model()
    return _target_model(provider, requested_model)


def query_ai(
    prompt: str,
    model: Optional[str] = None,
    format_json: bool = False,
    temperature: Optional[float] = None,
    timeout: Optional[int] = None,
    num_predict: Optional[int] = None,
    num_ctx: Optional[int] = None,
) -> Tuple[Optional[str], bool, Optional[str]]:
    """Query the selected provider and record privacy-safe usage metadata."""
    primary = _normalize_provider(getattr(settings, "AI_PROVIDER", "ollama"))
    started_at = time.perf_counter()
    result = _query_provider(primary, prompt, model, format_json, temperature, timeout, num_predict, num_ctx)
    _record_usage_event(
        primary,
        _effective_model(primary, model),
        int((time.perf_counter() - started_at) * 1000),
        result,
        fallback_used=False,
    )
    if result[1]:
        return result[:3]

    logger.warning("AI provider %s request failed: %s", primary, result[2])
    fallback = _normalize_provider(getattr(settings, "AI_FALLBACK_PROVIDER", ""))
    if not fallback or fallback == primary:
        return result[:3]

    fallback_started_at = time.perf_counter()
    fallback_result = _query_provider(
        fallback, prompt, model, format_json, temperature, timeout, num_predict, num_ctx
    )
    _record_usage_event(
        fallback,
        _effective_model(fallback, model),
        int((time.perf_counter() - fallback_started_at) * 1000),
        fallback_result,
        fallback_used=True,
    )
    if fallback_result[1]:
        return fallback_result[:3]
    logger.warning("AI provider fallback %s request failed: %s", fallback, fallback_result[2])
    return None, False, f"{primary} request failed; {fallback} fallback failed."

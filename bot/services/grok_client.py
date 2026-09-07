from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Any

import aiohttp

from bot.config import config

logger = logging.getLogger(__name__)


class GrokError(RuntimeError):
    pass


def _extract_json(text: str) -> dict[str, Any]:
    """Pull a JSON object out of a model reply, tolerating ```json fences."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(json)?", "", cleaned).rstrip("`").strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise GrokError(f"no JSON object found in reply: {text[:200]!r}")
    return json.loads(cleaned[start : end + 1])


async def ask_grok(
    session: aiohttp.ClientSession,
    system_prompt: str,
    user_message: str,
    *,
    model: str | None = None,
) -> dict[str, Any] | None:
    """Calls Grok with a system+user prompt pair, expects a JSON object back.

    Returns None (never raises) on any failure — callers are responsible for
    treating a None result as "assume the worst", per the pessimistic-fallback
    rule: a broken check should never silently pass a token through.
    """
    if not config.grok_api_key:
        logger.warning("GROK_API_KEY not set, skipping Grok call")
        return None

    payload = {
        "model": model or config.grok_fast_model,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
    }
    headers = {"Authorization": f"Bearer {config.grok_api_key}", "Content-Type": "application/json"}

    for attempt in range(config.grok_max_retries):
        try:
            async with session.post(
                config.grok_base_url,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=config.grok_timeout_seconds),
            ) as resp:
                if resp.status == 429 or resp.status >= 500:
                    await asyncio.sleep(1.5 * (attempt + 1))
                    continue
                resp.raise_for_status()
                body = await resp.json()
                content = body["choices"][0]["message"]["content"]
                return _extract_json(content)
        except (aiohttp.ClientError, asyncio.TimeoutError, KeyError, IndexError, json.JSONDecodeError, GrokError) as exc:
            logger.warning("Grok call failed (attempt %d/%d): %s", attempt + 1, config.grok_max_retries, exc)
            await asyncio.sleep(0.5 * (attempt + 1))

    return None

from __future__ import annotations

import asyncio
import logging
from typing import Protocol, Sequence

from bot.services.storage import Storage

logger = logging.getLogger(__name__)


class Encoder(Protocol):
    def encode(self, sentences: Sequence[str], *, normalize_embeddings: bool = False): ...


_model: Encoder | None = None
_load_attempted = False


def _load_model() -> Encoder | None:
    global _model, _load_attempted
    if _load_attempted:
        return _model
    _load_attempted = True
    try:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    except (ImportError, OSError, RuntimeError) as exc:
        logger.warning(
            "semantic copycat matching unavailable (%s); using normalized exact matching only", exc
        )
    return _model


def _label(symbol: str | None, name: str | None) -> str:
    return " ".join(part.strip() for part in (symbol or "", name or "") if part.strip())


def semantic_matches(
    symbol: str | None,
    name: str | None,
    candidates: list[tuple[str, str | None, str | None]],
    model: Encoder,
    threshold: float,
) -> list[tuple[str, float]]:
    target = _label(symbol, name)
    labelled = [(mint, _label(other_symbol, other_name)) for mint, other_symbol, other_name in candidates]
    labelled = [(mint, text) for mint, text in labelled if text]
    if not target or not labelled:
        return []
    embeddings = model.encode(
        [target, *(text for _, text in labelled)], normalize_embeddings=True
    )
    target_vector = embeddings[0]
    matches: list[tuple[str, float]] = []
    for (mint, _), vector in zip(labelled, embeddings[1:]):
        similarity = sum(float(left) * float(right) for left, right in zip(target_vector, vector))
        if similarity >= threshold:
            matches.append((mint, similarity))
    return matches


async def find_semantic_copycats(
    storage: Storage,
    symbol: str | None,
    name: str | None,
    since_seconds: int,
    exclude_mint: str,
    chain: str,
    threshold: float,
) -> list[tuple[str, float]]:
    model = await asyncio.to_thread(_load_model)
    if model is None:
        return []
    candidates = await storage.recent_token_names(since_seconds, exclude_mint, chain)
    return await asyncio.to_thread(semantic_matches, symbol, name, candidates, model, threshold)

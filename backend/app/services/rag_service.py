"""
RAG Service
===========
Semantic search via Qdrant for:
  - Knowledge base articles (KB)
  - Similar past resolved tickets

Uses BGE-small-en-v1.5 embeddings (384-dim) via the embedding_service.

Improvements over original:
  - Singleton async Qdrant client (no connection-per-request)
  - Deterministic point IDs via hashlib (not Python hash())
  - Config from centralized settings (not os.getenv)
"""

import hashlib
import logging
from typing import Optional

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import PointStruct, Distance, VectorParams

from app.core.config import settings
from app.services.embedding_service import encode

logger = logging.getLogger(__name__)

# ── Collections ───────────────────────────────────────────────────────────────
TICKETS_COL = settings.QDRANT_COLLECTION_TICKETS
KB_COL = settings.QDRANT_COLLECTION_KB
VECTOR_SIZE = settings.EMBEDDING_DIM  # 384 for BGE-small-en-v1.5

# ── Singleton async client ────────────────────────────────────────────────────
_client: Optional[AsyncQdrantClient] = None


def _qdrant_url() -> str:
    return f"http://{settings.QDRANT_HOST}:{settings.QDRANT_PORT}"


async def get_client() -> AsyncQdrantClient:
    global _client
    if _client is None:
        _client = AsyncQdrantClient(
            url=_qdrant_url(),
            api_key=settings.QDRANT_API_KEY or None,
        )
        logger.info(f"[RAG] Connected to Qdrant at {_qdrant_url()}")
    return _client


def _deterministic_point_id(identifier: str) -> int:
    """Generate a deterministic, collision-resistant point ID from a string.

    Uses SHA-256 instead of Python's hash() which is randomized per process
    (PYTHONHASHSEED). This ensures the same ticket_id always maps to the same
    point_id, even across restarts.
    """
    return int(hashlib.sha256(identifier.encode()).hexdigest()[:16], 16)


# ── Collection management ────────────────────────────────────────────────────


async def ensure_collections():
    client = await get_client()
    existing = [c.name for c in (await client.get_collections()).collections]
    for col in [TICKETS_COL, KB_COL]:
        if col not in existing:
            await client.create_collection(
                collection_name=col,
                vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
            )
            logger.info(f"[RAG] Created collection: {col}")


# ── Upsert ────────────────────────────────────────────────────────────────────


async def upsert_ticket(ticket_id: str, text: str, payload: dict):
    try:
        client = await get_client()
        vector = encode(text)
        point_id = _deterministic_point_id(ticket_id)
        await client.upsert(
            collection_name=TICKETS_COL,
            wait=True,
            points=[
                PointStruct(
                    id=point_id,
                    vector=vector,
                    payload={**payload, "ticket_id": ticket_id},
                )
            ],
        )
        logger.info(f"[RAG] Upserted ticket {ticket_id}")
    except Exception as e:
        logger.error(f"[RAG] upsert_ticket failed: {e}")


async def upsert_kb_article(
    article_id: str, title: str, content: str, metadata: dict = {}
):
    try:
        client = await get_client()
        text = f"{title}. {content}"
        vector = encode(text)
        point_id = _deterministic_point_id(article_id)
        await client.upsert(
            collection_name=KB_COL,
            wait=True,
            points=[
                PointStruct(
                    id=point_id,
                    vector=vector,
                    payload={
                        "article_id": article_id,
                        "title": title,
                        "content": content[:500],
                        **metadata,
                    },
                )
            ],
        )
        logger.info(f"[RAG] Upserted KB article: {article_id}")
    except Exception as e:
        logger.error(f"[RAG] upsert_kb_article failed: {e}")


# ── Search ────────────────────────────────────────────────────────────────────


async def search_kb(query_text: str, top_k: int = 5) -> list[dict]:
    try:
        client = await get_client()
        vector = encode(query_text)
        results = await client.search(
            collection_name=KB_COL,
            query_vector=vector,
            limit=top_k,
            score_threshold=0.6,
        )
        return [{**r.payload, "score": r.score} for r in results]
    except Exception as e:
        logger.error(f"[RAG] search_kb failed: {e}")
        return []


async def search_similar_tickets(query_text: str, top_k: int = 5) -> list[dict]:
    try:
        client = await get_client()
        vector = encode(query_text)
        results = await client.search(
            collection_name=TICKETS_COL,
            query_vector=vector,
            limit=top_k,
            score_threshold=0.7,
        )
        return [{**r.payload, "score": round(r.score, 3)} for r in results]
    except Exception as e:
        logger.error(f"[RAG] search_similar_tickets failed: {e}")
        return []

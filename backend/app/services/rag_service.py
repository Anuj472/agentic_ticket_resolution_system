import uuid, logging
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Distance, VectorParams
from app.services.embedding_service import encode
import os
logger = logging.getLogger(__name__)
QDRANT_URL      = os.getenv("QDRANT_URL", "http://qdrant:6333")
QDRANT_API_KEY  = os.getenv("QDRANT_API_KEY", "")
TICKETS_COL     = "tickets"
KB_COL          = "knowledge_base"
VECTOR_SIZE     = 384  # BGE-small-en-v1.5
def get_client() -> QdrantClient:
    return QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY or None)
def ensure_collections():
    client = get_client()
    existing = [c.name for c in client.get_collections().collections]
    for col in [TICKETS_COL, KB_COL]:
        if col not in existing:
            client.create_collection(
                collection_name=col,
                vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
            )
            logger.info(f"[RAG] Created collection: {col}")
async def upsert_ticket(ticket_id: str, text: str, payload: dict):
    try:
        client  = get_client()
        vector  = encode(text)
        point_id = abs(hash(ticket_id)) % (2**63)
        client.upsert(
            collection_name=TICKETS_COL,
            wait=True,
            points=[PointStruct(
                id=point_id,
                vector=vector,
                payload={**payload, "ticket_id": ticket_id},
            )],
        )
        logger.info(f"[RAG] Upserted ticket {ticket_id}")
    except Exception as e:
        logger.error(f"[RAG] upsert_ticket failed: {e}")
async def search_kb(query_text: str, top_k: int = 5) -> list[dict]:
    try:
        client = get_client()
        vector = encode(query_text)
        results = client.search(
            collection_name=KB_COL,
            query_vector=vector,
            limit=top_k,
            score_threshold=0.6,
        )
        return [
            {**r.payload, "score": r.score}
            for r in results
        ]
    except Exception as e:
        logger.error(f"[RAG] search_kb failed: {e}")
        return []
async def search_similar_tickets(query_text: str, top_k: int = 5) -> list[dict]:
    try:
        client = get_client()
        vector = encode(query_text)
        results = client.search(
            collection_name=TICKETS_COL,
            query_vector=vector,
            limit=top_k,
            score_threshold=0.7,
        )
        return [
            {**r.payload, "score": round(r.score, 3)}
            for r in results
        ]
    except Exception as e:
        logger.error(f"[RAG] search_similar_tickets failed: {e}")
        return []
async def upsert_kb_article(article_id: str, title: str, content: str, metadata: dict = {}):
    try:
        client   = get_client()
        text     = f"{title}. {content}"
        vector   = encode(text)
        point_id = abs(hash(article_id)) % (2**63)
        client.upsert(
            collection_name=KB_COL,
            wait=True,
            points=[PointStruct(
                id=point_id,
                vector=vector,
                payload={"article_id": article_id, "title": title, "content": content[:500], **metadata},
            )],
        )
        logger.info(f"[RAG] Upserted KB article: {article_id}")
    except Exception as e:
        logger.error(f"[RAG] upsert_kb_article failed: {e}")

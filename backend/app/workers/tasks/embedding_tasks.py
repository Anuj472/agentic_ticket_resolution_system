from app.workers.celery_app import celery_app
import logging

logger = logging.getLogger(__name__)


@celery_app.task(name="embedding_tasks.embed_ticket")
def embed_ticket(ticket_id: str, text: str):
    """BGE encode + Qdrant upsert (Phase 2)."""
    logger.info(f"[EMBED] Ticket {ticket_id}")
    return {"ticket_id": ticket_id, "note": "Phase 2 pending"}


@celery_app.task(name="embedding_tasks.embed_kb_article")
def embed_kb_article(article_id: str, text: str):
    logger.info(f"[EMBED] KB article {article_id}")
    return {"article_id": article_id, "note": "Phase 2 pending"}


@celery_app.task(name="embedding_tasks.reindex_all")
def reindex_all():
    logger.info("[EMBED] Reindexing all tickets")
    return {"status": "started"}

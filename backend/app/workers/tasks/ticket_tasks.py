"""
Celery Ticket Processing Task
==============================
Bridges sync Celery with the async LangGraph ticket_agent.
The full 6-node agentic pipeline (intake→classify→rag→route→resolve/escalate→close)
runs via ticket_agent.ainvoke(), then DB is updated from the final state.
"""

from __future__ import annotations
import asyncio
import logging
from datetime import datetime, timezone

from celery import shared_task
from sqlalchemy import select

from app.agents.state import TicketAgentState
from app.agents.ticket_agent import ticket_agent
from app.core.database import AsyncSessionLocal
from app.models.ticket import Ticket, TicketStatus, TicketPriority

logger = logging.getLogger(__name__)


# ── Helper ─────────────────────────────────────────────────────────────────────


def _parse_priority(raw: str | None) -> TicketPriority:
    """Safely coerce a string to TicketPriority enum."""
    if not raw:
        return TicketPriority.MEDIUM
    mapping = {p.value.lower(): p for p in TicketPriority}
    return mapping.get(raw.lower(), TicketPriority.MEDIUM)


# ── Core async pipeline ────────────────────────────────────────────────────────


async def _run_agent_pipeline(ticket_id: str) -> None:
    """Fetch ticket, run LangGraph agent, write results back to DB."""
    async with AsyncSessionLocal() as db:
        # ── 1. Fetch ticket ──────────────────────────────────────────────
        result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
        ticket = result.scalar_one_or_none()
        if not ticket:
            logger.error(f"[TASK] Ticket {ticket_id} not found")
            return

        logger.info(f"[TASK] Starting agent pipeline for {ticket.ticket_number}")

        # ── 2. Build initial state ───────────────────────────────────────
        initial_state: TicketAgentState = {
            "ticket_id": str(ticket.id),
            "title": ticket.title,
            "description": ticket.description,
            # Classification
            "category": None,
            "sub_category": None,
            "priority": None,
            "sentiment": None,
            "urgency_score": None,
            "ai_summary": None,
            "keywords": [],
            "embedding_category": None,
            "embedding_confidence": None,
            "category_confidence": None,
            # RAG
            "kb_results": [],
            "similar_tickets": [],
            "similar_ticket_count": 0,
            # Routing
            "routing_decision": None,
            "routing_reason": None,
            "routing_confidence": None,
            "assigned_department": None,
            "suggest_automation": False,
            "automation_candidate": False,
            "automation_reason": None,
            "repeat_issue": False,
            # Resolution
            "suggested_solution": None,
            # Escalation
            "is_escalated": False,
            "escalation_reason": None,
            # Audit
            "assigned_agent_id": None,
            "steps": [],
            "error": None,
        }

        # ── 3. Run LangGraph agent ───────────────────────────────────────
        try:
            final_state: TicketAgentState = await ticket_agent.ainvoke(initial_state)
        except Exception as e:
            logger.error(
                f"[TASK] Agent pipeline failed for {ticket.ticket_number}: {e}"
            )
            final_state = {**initial_state, "error": str(e)}

        # ── 4. Write results back to DB ──────────────────────────────────
        now = datetime.now(timezone.utc)

        # Classification
        if final_state.get("category"):
            ticket.category = final_state["category"]
            ticket.sub_category = final_state.get("sub_category")
            ticket.category_confidence = final_state.get("category_confidence")
            ticket.urgency_score = final_state.get("urgency_score")
            ticket.sentiment_score = final_state.get("sentiment_score")
            ticket.ai_summary = final_state.get("ai_summary")

        # Priority — only update if AI is more confident
        if final_state.get("priority"):
            ticket.priority = _parse_priority(final_state["priority"])
            ticket.predicted_priority = final_state["priority"]

        # RAG
        ticket.rag_kb_articles = final_state.get("kb_results", [])

        # Resolution
        if final_state.get("suggested_solution"):
            ticket.ai_suggested_solution = final_state["suggested_solution"]

        # Routing signals
        ticket.routing_confidence = final_state.get("routing_confidence")
        ticket.routing_reason = final_state.get("routing_reason")
        ticket.assigned_department = final_state.get("assigned_department")
        ticket.repeat_issue = final_state.get("repeat_issue", False)
        ticket.automation_candidate = final_state.get("automation_candidate", False)
        ticket.similar_ticket_count = final_state.get("similar_ticket_count", 0)

        # Escalation
        ticket.is_escalated = final_state.get("is_escalated", False)
        ticket.escalation_reason = final_state.get("escalation_reason")

        # Status & timestamps
        routing = final_state.get("routing_decision", "L1")
        if routing in ("auto_resolve", "automated_answer"):
            ticket.status = TicketStatus.RESOLVED
            ticket.resolved_at = now
        elif routing == "escalate":
            ticket.status = TicketStatus.IN_PROGRESS
        else:
            ticket.status = TicketStatus.IN_PROGRESS

        ticket.updated_at = now

        await db.commit()
        logger.info(
            f"[TASK] Completed {ticket.ticket_number}: "
            f"route={routing} escalated={ticket.is_escalated} "
            f"automation={ticket.automation_candidate}"
        )


# ── Celery task ────────────────────────────────────────────────────────────────


@shared_task(
    name="ticket_tasks.process_new_ticket",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    acks_late=True,
)
def process_new_ticket(self, ticket_id: str) -> dict:
    """Celery entry point: run async LangGraph pipeline synchronously."""
    try:
        asyncio.run(_run_agent_pipeline(ticket_id))
        return {"status": "success", "ticket_id": ticket_id}
    except Exception as exc:
        logger.error(f"[TASK] process_new_ticket failed ({ticket_id}): {exc}")
        raise self.retry(exc=exc)

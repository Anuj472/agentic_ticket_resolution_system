"""
Resolution Node (Node 5)
========================
Generates an AI solution using:
  - KB articles (knowledge base)
  - Similar past resolved tickets (RAG)

If the ticket is an automated_answer (high confidence + repeat issue),
the solution is built primarily from past resolutions.
"""

from __future__ import annotations
import logging

from app.agents.state import TicketAgentState
from app.services.llm_service import generate_solution

logger = logging.getLogger(__name__)


async def resolution_node(state: TicketAgentState) -> TicketAgentState:
    """Node 5: Generate AI solution using KB articles + past similar tickets."""
    try:
        kb_articles = state.get("kb_results", [])
        similar_tickets = state.get("similar_tickets", [])
        automated = state.get("routing_decision") == "automated_answer"

        solution = await generate_solution(
            title=state["title"],
            description=state["description"],
            kb_articles=kb_articles,
            similar_tickets=similar_tickets,
            automated=automated,
        )

        state["suggested_solution"] = solution
        state["steps"].append(
            f"resolution_generated automated={automated} "
            f"kb_count={len(kb_articles)} past_count={len(similar_tickets)}"
        )
        logger.info(
            f"[NODE] resolution_node done — ticket={state['ticket_id']} "
            f"automated={automated} kb={len(kb_articles)} past={len(similar_tickets)}"
        )
    except Exception as e:
        state["error"] = str(e)
        logger.error(f"[NODE] resolution_node failed: {e}", exc_info=True)

    return state

"""
RAG Node (Node 3)
=================
Searches two Qdrant collections in parallel:
  1. knowledge_base  — KB articles relevant to the ticket
  2. tickets         — similar past resolved tickets

Sets:
  - state["kb_results"]           list of KB article dicts
  - state["similar_tickets"]      list of past ticket dicts
  - state["similar_ticket_count"] int — used by routing node
  - state["repeat_issue"]         bool — True if ≥ 2 similar past tickets
"""
from app.agents.state import TicketAgentState
from app.services.rag_service import search_kb, search_similar_tickets
import asyncio
import logging

logger = logging.getLogger(__name__)

# Thresholds
SIMILAR_TICKET_REPEAT_THRESHOLD = 2   # ≥ this many → mark as repeat issue
SIMILAR_TICKET_AUTOMATION_THRESHOLD = 3  # ≥ this many → suggest automation


async def rag_node(state: TicketAgentState) -> TicketAgentState:
    """Node 3: retrieve KB articles + similar past tickets via BGE + Qdrant."""
    query = f"{state['title']}. {state['description'][:400]}"

    # Run both searches concurrently
    kb_hits, similar_hits = await asyncio.gather(
        search_kb(query, top_k=5),
        search_similar_tickets(query, top_k=5),
    )

    state["kb_results"]           = kb_hits
    state["similar_tickets"]      = similar_hits
    state["similar_ticket_count"] = len(similar_hits)
    state["repeat_issue"]         = len(similar_hits) >= SIMILAR_TICKET_REPEAT_THRESHOLD

    state["steps"].append(
        f"rag: kb_hits={len(kb_hits)} similar={len(similar_hits)} "
        f"repeat={state['repeat_issue']}"
    )
    logger.info(
        f"[NODE] rag_node: {len(kb_hits)} KB articles, "
        f"{len(similar_hits)} similar tickets, "
        f"repeat={state['repeat_issue']}"
    )
    return state

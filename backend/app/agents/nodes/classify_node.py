"""
Classify Node (Node 2)
======================
Runs two classifiers in parallel:

  1. GPT (LLM) — category, sub_category, priority, sentiment,
                  urgency_score, summary, keywords

  2. BGE centroid classifier (local embedding) — secondary category + confidence
     Falls back gracefully if the BGE model is not available.

The final category is the LLM prediction; embedding confidence is stored
as a secondary signal used in the routing node's combined confidence score.
If LLM and embedding agree → confidence boosted +8%.
If they disagree          → confidence penalised −10%.
"""

from __future__ import annotations
import asyncio
import logging

from app.agents.state import TicketAgentState
from app.services.llm_service import classify_ticket

logger = logging.getLogger(__name__)


def _embedding_classify_safe(title: str, description: str) -> dict:
    """Run BGE centroid classifier; return zero-confidence dict on failure."""
    try:
        from app.services.embedding_service import embedding_classify

        return embedding_classify(title, description)
    except Exception as e:
        logger.warning(
            f"[NODE] classify_node: embedding classifier unavailable ({e}) — using LLM only"
        )
        return {"category": None, "confidence": 0.0, "scores": {}}


async def classify_node(state: TicketAgentState) -> TicketAgentState:
    """Node 2: classify ticket with GPT + optional BGE embedding centroid."""
    title = state["title"]
    description = state["description"]

    # Run LLM + embedding concurrently (embedding runs in thread pool)
    llm_result, embed_result = await asyncio.gather(
        classify_ticket(title, description),
        asyncio.to_thread(_embedding_classify_safe, title, description),
    )

    # ── LLM results ───────────────────────────────────────────────────────
    state["category"] = llm_result.get("category", "Application")
    state["sub_category"] = llm_result.get("sub_category", "")
    state["priority"] = llm_result.get("priority", "medium")
    state["sentiment"] = llm_result.get("sentiment", "neutral")
    state["urgency_score"] = llm_result.get("urgency_score", 0.5)
    state["ai_summary"] = llm_result.get("summary", "")
    state["keywords"] = llm_result.get("keywords", [])

    # ── Embedding results ──────────────────────────────────────────────────
    embed_cat = embed_result.get("category")
    embed_conf = float(embed_result.get("confidence", 0.0))

    state["embedding_category"] = embed_cat
    state["embedding_confidence"] = round(embed_conf, 3)

    # Combined confidence — agreement/disagreement adjustment
    if embed_conf > 0.0 and embed_cat:
        agreement = state["category"] == embed_cat
        combined = embed_conf + 0.08 if agreement else max(embed_conf - 0.10, 0.3)
        state["category_confidence"] = round(min(combined, 1.0), 3)
    else:
        # BGE unavailable — use a neutral default; LLM confidence used by routing
        state["category_confidence"] = 0.0

    state["steps"].append(
        f"classified:{state['category']}/{state['priority']} "
        f"embed:{embed_cat}(conf={embed_conf:.2f}) "
        f"combined:{state['category_confidence']:.2f}"
    )
    logger.info(
        f"[NODE] classify_node → LLM={state['category']} "
        f"Embed={embed_cat}(conf={embed_conf:.2f}) "
        f"combined_conf={state['category_confidence']:.2f}"
    )
    return state

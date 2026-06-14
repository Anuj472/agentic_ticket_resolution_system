"""
Escalation Node (Node 6 — conditional)
=======================================
Reached when routing_decision == "escalate".
Sets is_escalated=True and writes a human-readable escalation reason.
"""

from app.agents.state import TicketAgentState
import logging

logger = logging.getLogger(__name__)


async def escalation_node(state: TicketAgentState) -> TicketAgentState:
    """Node 6: mark ticket escalated with a clear, actionable reason."""
    state["is_escalated"] = True

    # Build reason from available context
    priority = (state.get("priority") or "unknown").upper()
    confidence = state.get("routing_confidence")
    category = state.get("category", "Unknown")

    if confidence is not None and confidence < 0.65:
        reason = (
            f"Escalated due to low routing confidence ({confidence:.0%}). "
            f"The AI could not determine the correct resolution path with sufficient "
            f"certainty. A human specialist in {category} should review this ticket."
        )
    elif priority == "CRITICAL":
        reason = (
            f"Critical priority {category} ticket. Immediate specialist intervention "
            f"required. SLA breach risk is high."
        )
    else:
        reason = (
            f"Escalated to human agent. Category: {category}, Priority: {priority}. "
            f"Routing confidence: {f'{confidence:.0%}' if confidence else 'N/A'}."
        )

    state["escalation_reason"] = reason
    state["steps"].append(f"escalated: {reason[:80]}...")
    logger.info(
        f"[NODE] escalation_node: ticket {state['ticket_id']} escalated — {reason[:60]}"
    )
    return state

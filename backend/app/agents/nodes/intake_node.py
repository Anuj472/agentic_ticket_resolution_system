from app.agents.state import TicketAgentState
from app.services.nlp_service import preprocess, strip_pii
import logging

logger = logging.getLogger(__name__)


async def intake_node(state: TicketAgentState) -> TicketAgentState:
    """Node 1: Preprocess and strip PII from ticket text."""
    try:
        # preprocess() takes (title, description) and returns a dict
        result = preprocess(state["title"], state["description"])

        # Sanitize title (strip PII only, keep readable)
        state["title"] = strip_pii(state["title"])
        # Use the cleaned combined text as description for downstream nodes
        state["description"] = result["cleaned_text"]

        state["steps"].append("intake_done")
        logger.info(f"[NODE] intake_node done for ticket {state['ticket_id']}")
    except Exception as e:
        state["error"] = str(e)
        logger.error(f"[NODE] intake_node failed: {e}")
    return state

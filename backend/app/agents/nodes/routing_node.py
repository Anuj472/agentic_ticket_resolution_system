"""
Routing Node (Node 4)
=====================
Decision tree (applied in order):

  1. EMBEDDING CONFIDENCE  — from BGE centroid classifier (0–1)
     + LLM ROUTING CONFIDENCE — from GPT routing decision (0–1)
     Combined confidence = (embed_conf + llm_conf) / 2

  2. ROUTING DECISIONS:
     ┌─ repeat_issue AND combined_confidence >= 0.90
     │    → "automated_answer"  (pull from past resolutions, no human needed)
     │
     ├─ combined_confidence >= 0.90 AND NOT critical
     │    → "auto_resolve"     (high-confidence AI solution suggested to user)
     │
     ├─ combined_confidence < 0.65 OR priority == "critical"
     │    → "escalate"         (uncertain or critical → human review)
     │
     └─ otherwise
          → "L1"               (standard L1 human review)

  3. AUTOMATION FLAG — if similar_ticket_count >= 3, flag for runbook automation
"""

from __future__ import annotations
import logging

from app.agents.state import TicketAgentState
from app.services.llm_service import routing_decision

logger = logging.getLogger(__name__)

DEPARTMENT_MAP = {
    "Infrastructure": "Infrastructure & Cloud Team",
    "Application": "Application Support Team",
    "Security": "Security Operations Centre",
    "Database": "Database Administration Team",
    "Network": "Network Operations Centre",
    "Access Management": "Identity & Access Management Team",
}

# ── Thresholds ────────────────────────────────────────────────────────────────
CONFIDENCE_THRESHOLD = 0.90  # below this → escalate (human review)
AUTOMATION_THRESHOLD = 5  # similar_ticket_count > this → suggest automation


async def routing_node(state: TicketAgentState) -> TicketAgentState:
    """Node 4: Confidence-based routing with automated-answer for repeat issues."""
    try:
        category = state.get("category", "Application")
        priority = (state.get("priority") or "medium").lower()
        embed_conf = float(state.get("embedding_confidence", 0.7))
        similar_count = int(state.get("similar_ticket_count", 0))
        repeat_issue = bool(state.get("repeat_issue", False))

        # ── Step 1: Get LLM routing decision ─────────────────────────────
        llm_decision = await routing_decision(
            {
                "category": category,
                "sub_category": state.get("sub_category"),
                "priority": priority,
                "summary": state.get("ai_summary", ""),
                "kb_solution_found": bool(state.get("kb_results")),
                "sentiment": state.get("sentiment", "neutral"),
                "similar_count": similar_count,
            }
        )
        llm_conf = float(llm_decision.get("confidence", 0.7))
        _llm_route = llm_decision.get("route_to", "L1")

        # ── Step 2: Combine confidence signals ────────────────────────────
        # If embedding confidence was not computed (e.g. BGE unavailable), use LLM only
        if embed_conf == 0.0:
            combined_conf = llm_conf
        else:
            combined_conf = (embed_conf + llm_conf) / 2

        combined_conf = round(combined_conf, 2)

        state["routing_confidence"] = combined_conf

        # ── Step 3: Department assignment ────────────────────────────────
        state["assigned_department"] = DEPARTMENT_MAP.get(category, "L1 Support")

        # ── Step 4: Routing decision tree ────────────────────────────────────
        #
        #  Rule 1 — Critical priority always escalates (regardless of confidence)
        #  Rule 2 — confidence >= 0.90
        #             If repeated issue   → automated_answer  (pull from past resolutions)
        #             Else                → auto_resolve       (AI solution sent to user)
        #  Rule 3 — confidence < 0.90    → human_review
        #             Non-critical        → L1 (standard review queue)
        #             Critical (already caught by Rule 1)
        # ─────────────────────────────────────────────────────────────────────
        if priority == "critical":
            route = "escalate"
            reason = (
                f"🚨 ESCALATED — critical priority ticket. "
                f"Routed to {state['assigned_department']} for immediate human review."
            )

        elif (
            combined_conf >= CONFIDENCE_THRESHOLD
            or similar_count >= AUTOMATION_THRESHOLD
        ):
            if similar_count >= AUTOMATION_THRESHOLD:
                route = "automated_answer"
                reason = (
                    f"⚡ AUTOMATED RESPONSE — high repetition detected ({similar_count} similar tickets). "
                    f"Generating answer from past resolutions. No human needed."
                )
            elif repeat_issue and similar_count > 0:
                route = "automated_answer"
                reason = (
                    f"⚡ AUTOMATED RESPONSE — confidence {combined_conf:.2f} ≥ {CONFIDENCE_THRESHOLD} "
                    f"AND {similar_count} similar past tickets found. "
                    f"Generating answer from past resolutions. No human needed."
                )
            else:
                route = "auto_resolve"
                reason = (
                    f"✅ AUTO-RESOLVE — confidence {combined_conf:.2f} ≥ {CONFIDENCE_THRESHOLD}. "
                    f"AI solution is sufficiently reliable. Sending to user automatically."
                )
            logger.info(
                f"[NODE] routing_node: {route.upper()} (conf={combined_conf:.2f} ≥ {CONFIDENCE_THRESHOLD})"
            )

        else:
            # confidence < 0.90 → human review
            route = "escalate"
            reason = (
                f"👤 HUMAN REVIEW — confidence {combined_conf:.2f} < {CONFIDENCE_THRESHOLD}. "
                f"Model is not certain enough. Escalate to {state['assigned_department']} for human intervention."
            )
            logger.warning(
                f"[NODE] routing_node: HUMAN REVIEW — conf {combined_conf:.2f} < {CONFIDENCE_THRESHOLD} "
                f"(threshold). Ticket escalated."
            )

        state["routing_decision"] = route
        state["routing_reason"] = reason

        # ── Step 5: Automation suggestion ────────────────────────────────
        if repeat_issue and combined_conf >= CONFIDENCE_THRESHOLD:
            state["suggest_automation"] = True
            state["automation_candidate"] = True
            state["automation_reason"] = (
                f"Recurring issue with high confidence ({combined_conf}). "
                f"Recommend creating a runbook or automation script for: {category}."
            )
        else:
            state["suggest_automation"] = False
            state["automation_candidate"] = False
            state["automation_reason"] = None

        state["steps"].append(
            f"routed:{route} dept:{state['assigned_department']} "
            f"conf:{combined_conf:.2f} repeat:{repeat_issue}"
        )
        logger.info(
            f"[NODE] routing_node → {route} | dept={state['assigned_department']} "
            f"| conf={combined_conf:.2f} | repeat={repeat_issue}"
        )

    except Exception as e:
        logger.error(f"[NODE] routing_node failed: {e}", exc_info=True)
        state["routing_decision"] = "L1"
        state["routing_confidence"] = 0.5
        state["suggest_automation"] = False
        state["automation_candidate"] = False
        state["error"] = str(e)

    return state

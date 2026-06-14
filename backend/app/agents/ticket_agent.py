"""
Ticket Agent — LangGraph Pipeline
===================================
Full agentic workflow:

  intake ──► classify ──► rag ──► routing ──┬──► automated_answer ──► close
                                              ├──► resolution ──────────► close
                                              ├──► escalation ──────────► close
                                              └──► close  (L1 hand-off)

Routing decisions (from routing_node):
  automated_answer  — repeat issue + combined confidence ≥ 0.90
  auto_resolve      — combined confidence ≥ 0.90
  escalate          — combined confidence < 0.65 OR critical priority
  L1                — 0.65 ≤ confidence < 0.90 (human L1 review)
"""

from langgraph.graph import StateGraph, END

from app.agents.state import TicketAgentState
from app.agents.nodes.intake_node import intake_node
from app.agents.nodes.classify_node import classify_node
from app.agents.nodes.rag_node import rag_node
from app.agents.nodes.routing_node import routing_node
from app.agents.nodes.resolution_node import resolution_node
from app.agents.nodes.escalation_node import escalation_node
from app.agents.nodes.close_node import close_node


def route_after_routing(state: TicketAgentState) -> str:
    """Conditional edge: map routing_decision to next node."""
    decision = state.get("routing_decision", "L1")
    if decision == "automated_answer":
        return "resolution"  # resolution_node knows to use past-ticket context
    elif decision == "auto_resolve":
        return "resolution"
    elif decision == "escalate":
        return "escalation"
    else:
        # L1 — hand off to human; still generate a suggestion for the agent
        return "resolution"


def create_ticket_agent():
    graph = StateGraph(TicketAgentState)

    # Register all nodes
    graph.add_node("intake", intake_node)
    graph.add_node("classify", classify_node)
    graph.add_node("rag", rag_node)
    graph.add_node("routing", routing_node)
    graph.add_node("resolution", resolution_node)
    graph.add_node("escalation", escalation_node)
    graph.add_node("close", close_node)

    # Linear edges for the first 4 nodes
    graph.set_entry_point("intake")
    graph.add_edge("intake", "classify")
    graph.add_edge("classify", "rag")
    graph.add_edge("rag", "routing")

    # Conditional branching after routing
    graph.add_conditional_edges(
        "routing",
        route_after_routing,
        {
            "resolution": "resolution",
            "escalation": "escalation",
        },
    )

    # Both branches converge to close
    graph.add_edge("resolution", "close")
    graph.add_edge("escalation", "close")
    graph.add_edge("close", END)

    return graph.compile()


ticket_agent = create_ticket_agent()

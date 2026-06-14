from __future__ import annotations
from typing import TypedDict, Optional, List


class TicketAgentState(TypedDict):
    # ── Input ────────────────────────────────────────────────────────────────
    ticket_id: str
    title: str
    description: str

    # ── Classification (Node 2 — LLM + Embedding) ────────────────────────────
    category: Optional[str]  # final category (LLM-primary, embed-validated)
    sub_category: Optional[str]
    priority: Optional[str]  # critical | high | medium | low
    sentiment: Optional[str]  # frustrated | neutral | urgent | satisfied
    urgency_score: Optional[float]
    ai_summary: Optional[str]
    keywords: List[str]

    # Embedding-based classifier signal (BGE centroid cosine similarity)
    embedding_category: Optional[str]
    embedding_confidence: Optional[float]  # 0–1, cosine sim to best centroid
    category_confidence: Optional[float]  # combined final confidence

    # ── RAG (Node 3 — BGE + Qdrant) ─────────────────────────────────────────
    kb_results: List[dict]  # KB article hits [{title, content, score}]
    similar_tickets: List[dict]  # past resolved tickets [{title, resolution, score}]
    similar_ticket_count: int
    repeat_issue: bool  # True if ≥ 2 similar past tickets found

    # ── Routing (Node 4) ─────────────────────────────────────────────────────
    # Decision tree:
    #   automated_answer  → repeat + combined_conf >= 0.90
    #   auto_resolve      → combined_conf >= 0.90
    #   escalate          → combined_conf < 0.65 OR critical priority
    #   L1                → else (0.65 ≤ conf < 0.90)
    routing_decision: Optional[str]  # automated_answer|auto_resolve|escalate|L1
    routing_reason: Optional[str]  # human-readable reason for decision
    routing_confidence: Optional[float]  # combined (embed + LLM) confidence
    assigned_department: Optional[str]  # e.g. "Security Operations Centre"

    # Automation
    suggest_automation: bool
    automation_candidate: bool
    automation_reason: Optional[str]

    # ── Resolution (Node 5) ──────────────────────────────────────────────────
    suggested_solution: Optional[str]  # numbered step-by-step from GPT

    # ── Escalation (Node 6 — conditional) ───────────────────────────────────
    is_escalated: bool
    escalation_reason: Optional[str]

    # ── Audit trail ──────────────────────────────────────────────────────────
    assigned_agent_id: Optional[str]
    steps: List[str]  # ordered list of node decisions
    error: Optional[str]

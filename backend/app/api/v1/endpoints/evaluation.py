"""
Evaluation API Endpoints
========================
POST /evaluation/run     — trigger full eval in background (~60–90s)
GET  /evaluation/results — return latest cached results (404 until ready)
GET  /evaluation/samples — return the 30 ground-truth test tickets
"""

from __future__ import annotations
import asyncio
import logging
import traceback
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks

from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.evaluation_service import (
    GROUND_TRUTH,
    evaluate_classification,
    evaluate_semantic_similarity,
    evaluate_llm_judge,
)
from app.services.llm_service import generate_solution

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/evaluation", tags=["Evaluation"])

# ── In-process cache ──────────────────────────────────────────────────────────
_cached_results: dict | None = None
_running: bool = False


# ── Evaluation runner ─────────────────────────────────────────────────────────


async def _run_full_evaluation() -> None:
    """
    Full evaluation pipeline:
      1. Classification accuracy + F1  (30 ground-truth tickets)
      2. Semantic similarity           (BGE cosine, 10 samples)
      3. LLM-as-judge                  (GPT scores, 10 samples)
    Results written to module-level _cached_results.
    """
    global _cached_results, _running
    try:
        logger.info("[Eval] ═══════ Starting full evaluation run ═══════")

        # ── Step 1: Classification metrics ────────────────────────────────
        logger.info("[Eval] Step 1/3 — classification accuracy + F1")
        clf = await evaluate_classification()
        logger.info(
            f"[Eval] Classification done — accuracy={clf['accuracy_pct']}% "
            f"macro_f1={clf['macro_f1']}"
        )

        # ── Step 2: Generate solutions for semantic eval ──────────────────
        logger.info("[Eval] Step 2/3 — generating solutions (10 tickets)")
        sample = GROUND_TRUTH[:10]
        solutions = list(
            await asyncio.gather(
                *[generate_solution(t["title"], t["description"], []) for t in sample]
            )
        )
        references = [t["description"] for t in sample]
        sem = await evaluate_semantic_similarity(solutions, references)
        logger.info(f"[Eval] Semantic similarity done — mean={sem.get('mean')}")

        # ── Step 3: LLM-as-judge ─────────────────────────────────────────
        logger.info("[Eval] Step 3/3 — LLM-as-judge (10 tickets)")
        judge = await evaluate_llm_judge(sample, solutions, sample_size=10)
        logger.info(f"[Eval] LLM judge done — overall={judge.get('mean_overall')}")

        # ── Consolidate ───────────────────────────────────────────────────
        _cached_results = {
            "run_at": datetime.now(timezone.utc).isoformat(),
            "status": "complete",
            "classification": clf,
            "semantic_similarity": sem,
            "llm_judge": judge,
            "summary": {
                "accuracy_pct": clf["accuracy_pct"],
                "macro_f1": clf["macro_f1"],
                "semantic_similarity": sem.get("mean", 0.0),
                "llm_judge_overall": judge.get("mean_overall", 0.0),
            },
        }
        logger.info(
            f"[Eval] ═══════ Evaluation complete ═══════ "
            f"acc={clf['accuracy_pct']}% F1={clf['macro_f1']} "
            f"sem={sem.get('mean')} judge={judge.get('mean_overall')}"
        )
    except Exception:
        tb = traceback.format_exc()
        logger.error(f"[Eval] Evaluation FAILED:\n{tb}")
        _cached_results = {
            "run_at": datetime.now(timezone.utc).isoformat(),
            "status": "error",
            "error": tb,
        }
    finally:
        _running = False  # always release the lock


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.post("/run")
async def run_evaluation(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    """
    Trigger a full evaluation run in the background.
    Returns immediately; poll GET /evaluation/results every 5 s until ready.
    """
    global _running
    if _running:
        raise HTTPException(
            status_code=409,
            detail="Evaluation already in progress — check /evaluation/results in ~90s.",
        )
    _running = True
    background_tasks.add_task(_run_full_evaluation)
    return {
        "message": "Evaluation started. Poll GET /evaluation/results every 5 s — results appear in ~90 s.",
        "status": "started",
    }


@router.get("/results")
async def get_evaluation_results(
    current_user: User = Depends(get_current_user),
):
    """Return the latest cached evaluation results, or 404 if not ready yet."""
    if _cached_results is None:
        raise HTTPException(
            status_code=404,
            detail="No evaluation results yet — POST /evaluation/run to start.",
        )
    return _cached_results


@router.get("/samples")
async def get_eval_samples(
    current_user: User = Depends(get_current_user),
):
    """Return the 30 ground-truth test tickets used for evaluation."""
    return {"samples": GROUND_TRUTH, "total": len(GROUND_TRUTH)}

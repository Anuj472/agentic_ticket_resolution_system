"""
Evaluation Service
==================
Implements all 4 evaluation metrics required by the problem statement:

  1. Accuracy          — classification accuracy vs ground-truth labels
  2. F1 Score          — macro + per-class F1 (sklearn-style, no sklearn dep)
  3. Semantic Similarity — BGE cosine similarity between AI solution and reference
  4. LLM-as-Judge      — GPT-4.1-nano scores solution on relevance/correctness/completeness

Ground truth: 30 hand-crafted labeled tickets covering all 6 categories.
"""

from __future__ import annotations
import json
import logging
import math

from app.services.llm_service import classify_ticket, get_client
from app.core.config import settings

logger = logging.getLogger(__name__)

# ── Ground Truth Dataset (30 tickets, 5 per category) ─────────────────────────
GROUND_TRUTH: list[dict] = [
    # Infrastructure (5)
    {
        "title": "ESXi host unresponsive after patch Tuesday",
        "description": "VMware ESXi host stopped responding to management console after applying security patches. VMs are running but host management is unavailable.",
        "category": "Infrastructure",
        "priority": "critical",
    },
    {
        "title": "AWS EC2 instance CPU stuck at 100%",
        "description": "Production EC2 t3.large instance has been at 100% CPU for 3 hours. Auto-scaling not triggering. Application response time degraded.",
        "category": "Infrastructure",
        "priority": "high",
    },
    {
        "title": "NAS storage array showing degraded RAID",
        "description": "NetApp NAS showing one disk failed in RAID-5 array. One more disk failure would cause data loss. Rebuild is needed immediately.",
        "category": "Infrastructure",
        "priority": "critical",
    },
    {
        "title": "Server room temperature alarm triggered",
        "description": "Data centre temperature sensor reporting 35°C in rack row B. CRAC unit 2 offline. Risk of thermal shutdown for servers.",
        "category": "Infrastructure",
        "priority": "high",
    },
    {
        "title": "Backup job failing for 3 consecutive nights",
        "description": "Veeam backup job for SQL-PROD-01 has failed three nights running with error VSSControl:Backup job failed. No recent backup available.",
        "category": "Infrastructure",
        "priority": "high",
    },
    # Application (5)
    {
        "title": "SAP ERP throwing ABAP dump on PO creation",
        "description": "Users in procurement cannot create purchase orders. SAP is throwing a short dump: CONVT_NO_NUMBER on field BSART. Started after last weekend's transport.",
        "category": "Application",
        "priority": "critical",
    },
    {
        "title": "Salesforce Lightning page loading blank",
        "description": "After the Spring '24 release, the Opportunity detail page shows blank for all users in EMEA region. Console shows JavaScript error in LWC component.",
        "category": "Application",
        "priority": "high",
    },
    {
        "title": "Microsoft Teams calls dropping after 5 minutes",
        "description": "All Teams video calls are dropping exactly at the 5-minute mark. Audio continues but video freezes. Issue reproducible across all devices.",
        "category": "Application",
        "priority": "medium",
    },
    {
        "title": "Mobile app crashing on Android 14 devices",
        "description": "Company mobile app crashes immediately on launch for users who upgraded to Android 14. iOS users unaffected. Play Store rating dropped from 4.2 to 2.1.",
        "category": "Application",
        "priority": "high",
    },
    {
        "title": "Outlook calendar not syncing with Exchange",
        "description": "Multiple users reporting that calendar invites sent from external contacts are not appearing in Outlook. OWA shows the meetings correctly.",
        "category": "Application",
        "priority": "medium",
    },
    # Security (5)
    {
        "title": "Ransomware alert on finance workstation",
        "description": "CrowdStrike EDR blocked a ransomware execution on workstation FIN-WS-042. Process tree shows LockBit variant. File encryption was attempted on mapped drives.",
        "category": "Security",
        "priority": "critical",
    },
    {
        "title": "Phishing campaign targeting HR department",
        "description": "5 HR employees clicked a link in a spear-phishing email impersonating the CEO. Credentials may be compromised. Need immediate password resets and MFA verification.",
        "category": "Security",
        "priority": "critical",
    },
    {
        "title": "DLP alert: large data transfer to personal cloud",
        "description": "Symantec DLP flagged a 4.2GB upload from a developer laptop to a personal Dropbox account. The data includes source code repositories.",
        "category": "Security",
        "priority": "high",
    },
    {
        "title": "SSL certificate expired on customer portal",
        "description": "Customers reporting browser security warnings on the self-service portal. SSL certificate for portal.company.com expired 2 hours ago.",
        "category": "Security",
        "priority": "critical",
    },
    {
        "title": "Failed login brute force on admin account",
        "description": "Azure AD showing 847 failed login attempts against admin@company.com in the last 30 minutes from IPs in Eastern Europe. Account not yet locked.",
        "category": "Security",
        "priority": "critical",
    },
    # Database (5)
    {
        "title": "SQL Server deadlock killing production transactions",
        "description": "SQL Server 2019 production instance showing frequent deadlocks in the order processing database. Deadlock monitor shows 15 victims per hour.",
        "category": "Database",
        "priority": "critical",
    },
    {
        "title": "Oracle tablespace 98% full — application write errors",
        "description": "Oracle DB USERS tablespace is at 98% capacity. Application is now throwing ORA-01536 errors. Urgent space allocation required.",
        "category": "Database",
        "priority": "critical",
    },
    {
        "title": "PostgreSQL replication lag exceeding 30 minutes",
        "description": "Streaming replication lag between primary and standby PostgreSQL servers has grown to 32 minutes. DR readiness is compromised.",
        "category": "Database",
        "priority": "high",
    },
    {
        "title": "MongoDB query performance degraded after index drop",
        "description": "Application team accidentally dropped the compound index on the orders collection. Query response times degraded from 12ms to 8 seconds.",
        "category": "Database",
        "priority": "high",
    },
    {
        "title": "MySQL slow query log showing 45-second queries",
        "description": "MySQL slow query log is recording 200+ queries per hour taking over 45 seconds. Primary cause appears to be missing index on the customer_transactions table.",
        "category": "Database",
        "priority": "medium",
    },
    # Network (5)
    {
        "title": "VPN concentrator rejecting all connections after upgrade",
        "description": "After upgrading Cisco ASA from 9.14 to 9.16, all remote VPN users receive Authentication Failed errors. Certificate mismatch suspected.",
        "category": "Network",
        "priority": "critical",
    },
    {
        "title": "Core switch loop causing network storm",
        "description": "Spanning tree reconfiguration event caused a temporary loop on VLAN 10. Network traffic increased 10x. Some switches still showing high CPU.",
        "category": "Network",
        "priority": "critical",
    },
    {
        "title": "DNS resolution failing for internal domains",
        "description": "Users cannot resolve internal hostnames like intranet.company.local. External DNS works fine. Issue started after domain controller maintenance.",
        "category": "Network",
        "priority": "high",
    },
    {
        "title": "Wi-Fi dropping intermittently in Building C",
        "description": "Users in Building C floors 2-4 reporting Wi-Fi disconnections every 20-30 minutes. Rogue AP detected on same channel as corporate APs.",
        "category": "Network",
        "priority": "medium",
    },
    {
        "title": "BGP route flap causing intermittent internet outage",
        "description": "ISP BGP session going up/down repeatedly causing 30-second internet outages every 10 minutes. Affects all outbound internet traffic.",
        "category": "Network",
        "priority": "critical",
    },
    # Access Management (5)
    {
        "title": "Mass account lockout after AD password policy change",
        "description": "After changing the minimum password age policy, 300 user accounts were locked out simultaneously. Users cannot log in to any systems.",
        "category": "Access Management",
        "priority": "critical",
    },
    {
        "title": "New joiner cannot access any systems on day one",
        "description": "New employee starting today has no access to email, VPN, or internal systems. Onboarding ticket was raised 2 weeks ago but provisioning was not completed.",
        "category": "Access Management",
        "priority": "high",
    },
    {
        "title": "MFA not working for remote workers after Okta update",
        "description": "After Okta org-wide MFA enforcement update, 150 remote employees are locked out. Push notifications not arriving on their registered devices.",
        "category": "Access Management",
        "priority": "critical",
    },
    {
        "title": "Service account password expired breaking CI/CD pipeline",
        "description": "The Jenkins CI/CD service account password expired causing all build pipelines to fail with authentication errors to Git and Artifactory.",
        "category": "Access Management",
        "priority": "high",
    },
    {
        "title": "Contractor requires temporary elevated access for audit",
        "description": "External auditor needs read-only access to financial reports in SharePoint for 3 days. Requires approval workflow and time-limited provisioning.",
        "category": "Access Management",
        "priority": "low",
    },
]

CATEGORIES = [
    "Infrastructure",
    "Application",
    "Security",
    "Database",
    "Network",
    "Access Management",
]


# ── 1. Classification Metrics ─────────────────────────────────────────────────


def _compute_f1(tp: int, fp: int, fn: int) -> float:
    prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    return 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0


async def evaluate_classification() -> dict:
    """
    Run the LLM classifier on ground truth tickets, compute accuracy and F1.
    Returns per-class and macro-averaged metrics.
    """
    import asyncio

    predictions: list[str] = []
    ground_truth: list[str] = [t["category"] for t in GROUND_TRUTH]

    async def _classify_one(ticket: dict) -> str:
        result = await classify_ticket(ticket["title"], ticket["description"])
        return result.get("category", "Application")

    # Classify all concurrently (batches of 10 to avoid rate limits)
    batch_size = 10
    for i in range(0, len(GROUND_TRUTH), batch_size):
        batch = GROUND_TRUTH[i : i + batch_size]
        preds = await asyncio.gather(*[_classify_one(t) for t in batch])
        predictions.extend(preds)

    # Accuracy
    correct = sum(p == g for p, g in zip(predictions, ground_truth))
    accuracy = correct / len(ground_truth)

    # Per-class F1
    f1_per_class: dict[str, float] = {}
    for cat in CATEGORIES:
        tp = sum(1 for p, g in zip(predictions, ground_truth) if p == cat and g == cat)
        fp = sum(1 for p, g in zip(predictions, ground_truth) if p == cat and g != cat)
        fn = sum(1 for p, g in zip(predictions, ground_truth) if p != cat and g == cat)
        f1_per_class[cat] = round(_compute_f1(tp, fp, fn), 3)

    macro_f1 = round(sum(f1_per_class.values()) / len(f1_per_class), 3)

    return {
        "accuracy": round(accuracy, 3),
        "accuracy_pct": round(accuracy * 100, 1),
        "macro_f1": macro_f1,
        "f1_per_class": f1_per_class,
        "total_samples": len(ground_truth),
        "correct": correct,
        "predictions": predictions,
        "ground_truth": ground_truth,
    }


# ── 2. Semantic Similarity (OpenAI embeddings) ───────────────────────────────


def _dot(a: list[float], b: list[float]) -> float:
    """Cosine similarity for unit-normalised OpenAI embeddings."""
    return sum(x * y for x, y in zip(a, b))


async def _openai_embed(text: str) -> list[float]:
    """Get a unit-normalised embedding from OpenAI text-embedding-3-small."""
    resp = await get_client().embeddings.create(
        model="text-embedding-3-small",
        input=text[:2000],
    )
    vec = resp.data[0].embedding
    # L2-normalise
    norm = math.sqrt(sum(x * x for x in vec))
    return [x / norm for x in vec] if norm > 0 else vec


async def evaluate_semantic_similarity(
    generated_solutions: list[str],
    reference_solutions: list[str],
) -> dict:
    """
    Cosine similarity between AI solutions and reference descriptions
    using OpenAI text-embedding-3-small (no local model required).
    """
    import asyncio

    pairs = [
        (gen, ref)
        for gen, ref in zip(generated_solutions, reference_solutions)
        if gen and ref
    ]
    if not pairs:
        return {"mean": 0.0, "min": 0.0, "max": 0.0, "samples": 0}

    # Embed all texts concurrently
    all_texts = [p[0] for p in pairs] + [p[1] for p in pairs]
    embeddings = await asyncio.gather(*[_openai_embed(t) for t in all_texts])
    n = len(pairs)
    gen_vecs = embeddings[:n]
    ref_vecs = embeddings[n:]

    scores = [_dot(g, r) for g, r in zip(gen_vecs, ref_vecs)]

    mean_ = sum(scores) / len(scores)
    min_ = min(scores)
    max_ = max(scores)
    var_ = sum((s - mean_) ** 2 for s in scores) / len(scores)
    std_ = math.sqrt(var_)

    return {
        "mean": round(mean_, 3),
        "min": round(min_, 3),
        "max": round(max_, 3),
        "std": round(std_, 3),
        "samples": len(scores),
        "scores": [round(s, 3) for s in scores],
        "method": "openai/text-embedding-3-small",
    }


# ── 3. LLM-as-Judge ──────────────────────────────────────────────────────────

LLM_JUDGE_PROMPT = """You are an expert IT support quality evaluator.
Evaluate the AI-generated resolution for this IT ticket on three dimensions.

Ticket: {title}
Category: {category}
AI Resolution: {solution}

Score each dimension from 1 (very poor) to 10 (excellent):
- relevance: Does the resolution address the actual problem?
- correctness: Are the steps technically accurate and safe to follow?
- completeness: Does it cover all necessary steps to fully resolve the issue?

Respond ONLY with valid JSON:
{{"relevance": <1-10>, "correctness": <1-10>, "completeness": <1-10>, "overall": <1-10>, "feedback": "<one sentence>"}}"""


async def llm_judge_single(ticket: dict, solution: str) -> dict:
    """Ask GPT to evaluate one AI-generated solution."""
    try:
        prompt = LLM_JUDGE_PROMPT.format(
            title=ticket["title"],
            category=ticket["category"],
            solution=(solution or "No solution generated")[:600],
        )
        resp = await get_client().chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=200,
            response_format={"type": "json_object"},
        )
        scores = json.loads(resp.choices[0].message.content)
        return {
            "relevance": scores.get("relevance", 5),
            "correctness": scores.get("correctness", 5),
            "completeness": scores.get("completeness", 5),
            "overall": scores.get("overall", 5),
            "feedback": scores.get("feedback", ""),
        }
    except Exception as e:
        logger.error(f"[Eval] llm_judge failed: {e}")
        return {
            "relevance": 5,
            "correctness": 5,
            "completeness": 5,
            "overall": 5,
            "feedback": "Error",
        }


async def evaluate_llm_judge(
    tickets: list[dict],
    solutions: list[str],
    sample_size: int = 10,
) -> dict:
    """
    Run LLM-as-judge on a sample of tickets and their AI solutions.
    Averages scores across all dimensions.
    """
    import asyncio

    # Sample for cost efficiency
    paired = [(t, s) for t, s in zip(tickets, solutions) if s]
    sample = paired[:sample_size]

    results = await asyncio.gather(*[llm_judge_single(t, s) for t, s in sample])

    if not results:
        return {}

    def avg(key):
        return round(sum(r[key] for r in results) / len(results), 2)
    return {
        "mean_relevance": avg("relevance"),
        "mean_correctness": avg("correctness"),
        "mean_completeness": avg("completeness"),
        "mean_overall": avg("overall"),
        "sample_size": len(results),
        "details": results,
    }

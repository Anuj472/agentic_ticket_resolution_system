"""
Embedding Service
=================
- BGE-small-en-v1.5 sentence encoder (runs locally, zero API cost)
- Centroid-based embedding classifier for the 6 IT ticket categories
"""

from __future__ import annotations
import logging
import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# ── Model ─────────────────────────────────────────────────────────────────────
_model: SentenceTransformer | None = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer("BAAI/bge-small-en-v1.5")
        logger.info("[Embed] BGE-small-en-v1.5 loaded")
    return _model


def encode(text: str) -> list[float]:
    """Return a 384-dim unit-normalised embedding."""
    vec = get_model().encode(text, normalize_embeddings=True)
    return vec.tolist()


# ── Centroid Classifier ───────────────────────────────────────────────────────
# Each category is represented by a rich description sentence.
# At first call, centroids are computed once and cached.

CATEGORY_DESCRIPTIONS: dict[str, str] = {
    "Infrastructure": (
        "Server down, virtual machine crash, CPU overload, disk failure, "
        "cloud resource unavailable, data centre outage, hypervisor problem, "
        "bare metal hardware fault, RAID array degraded, memory error"
    ),
    "Application": (
        "Software crash, application not launching, ERP error, CRM bug, "
        "web application timeout, mobile app unresponsive, API returning 500, "
        "desktop software license expired, software update failure"
    ),
    "Security": (
        "Malware detected, phishing email, ransomware, data breach, "
        "suspicious login, brute force attack, unauthorised access, "
        "DLP alert, firewall rule violation, CVE vulnerability, SIEM alert"
    ),
    "Database": (
        "SQL Server down, Oracle connection timeout, database corruption, "
        "slow query performance, replication lag, index rebuild, "
        "deadlock detected, table lock, backup failure, storage full"
    ),
    "Network": (
        "VPN not connecting, network latency, packet loss, DNS resolution failure, "
        "Wi-Fi dropping, firewall blocking traffic, MPLS link down, "
        "BGP route flap, switch port down, DHCP lease exhausted"
    ),
    "Access Management": (
        "Password reset, account locked, MFA not working, SSO login failure, "
        "Active Directory permission, LDAP sync error, user provisioning, "
        "role assignment, group policy, certificate expired, SAML assertion"
    ),
}

_centroids: dict[str, np.ndarray] | None = None


def _get_centroids() -> dict[str, np.ndarray]:
    global _centroids
    if _centroids is None:
        model = get_model()
        _centroids = {
            cat: model.encode(desc, normalize_embeddings=True)
            for cat, desc in CATEGORY_DESCRIPTIONS.items()
        }
        logger.info("[Embed] Category centroids computed")
    return _centroids


def embedding_classify(title: str, description: str) -> dict:
    """
    Classify ticket using cosine similarity against category centroids.

    Returns:
        {
            "category":   str,    # predicted category
            "confidence": float,  # cosine similarity to best centroid (0–1)
            "scores":     dict    # similarity score per category
        }
    """
    text = f"{title}. {description[:400]}"
    vec = np.array(encode(text))
    centroids = _get_centroids()

    scores = {cat: float(np.dot(vec, centroid)) for cat, centroid in centroids.items()}
    best_cat = max(scores, key=scores.__getitem__)
    best_conf = scores[best_cat]

    logger.info(f"[Embed] Classified → {best_cat} (conf={best_conf:.3f})")
    return {"category": best_cat, "confidence": best_conf, "scores": scores}

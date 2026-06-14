import re

# PII patterns
_PII_PATTERNS = [
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"), "[EMAIL]"),
    (re.compile(r"\b(?:\+91|0)?[6-9]\d{9}\b"), "[PHONE]"),
    (re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"), "[IP_ADDR]"),
    (re.compile(r"\b[A-Z]{2}\d{2}[A-Z]{4}\d{7}[A-Z]{1}\b"), "[AADHAAR]"),
    (re.compile(r"password\s*[:=]\s*\S+", re.IGNORECASE), "password: [REDACTED]"),
    (re.compile(r"token\s*[:=]\s*\S+", re.IGNORECASE), "token: [REDACTED]"),
    (re.compile(r"secret\s*[:=]\s*\S+", re.IGNORECASE), "secret: [REDACTED]"),
]
_NOISE = re.compile(
    r"(please|kindly|asap|urgent|hello|hi|dear|thanks|thank you|regards|sincerely)",
    re.IGNORECASE,
)


def strip_pii(text: str) -> str:
    for pattern, replacement in _PII_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def clean_text(text: str) -> str:
    text = strip_pii(text)
    text = _NOISE.sub("", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_keywords(text: str) -> list[str]:
    """Simple keyword extraction without spaCy dependency."""
    stop_words = {
        "the",
        "a",
        "an",
        "is",
        "it",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "and",
        "or",
        "but",
        "not",
        "with",
        "this",
        "that",
        "have",
        "has",
        "had",
        "be",
        "been",
        "was",
        "were",
        "are",
        "will",
        "would",
        "could",
        "should",
        "from",
        "by",
        "as",
        "into",
        "about",
    }
    words = re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())
    seen = set()
    keywords = []
    for w in words:
        if w not in stop_words and w not in seen:
            seen.add(w)
            keywords.append(w)
    return keywords[:20]


def extract_entities(text: str) -> dict:
    """Extract structured entities using regex patterns."""
    entities = {
        "services": [],
        "error_codes": [],
        "urls": [],
        "ticket_refs": [],
    }
    # Service names (capitalized words)
    entities["services"] = re.findall(
        r"\b[A-Z][a-z]+ (?:Server|Service|Portal|Gateway|Cluster|Host)\b", text
    )
    # Error codes
    entities["error_codes"] = re.findall(
        r"\b(?:error|code|err)\s*[:\-]?\s*(\d{3,4})\b", text, re.IGNORECASE
    )
    # URLs
    entities["urls"] = re.findall(r"https?://\S+", text)
    # Ticket references
    entities["ticket_refs"] = re.findall(r"\b(?:TKT|INC|JIRA|CHG)-\d+\b", text)
    return entities


def preprocess(title: str, description: str) -> dict:
    combined = f"{title}. {description}"
    cleaned = clean_text(combined)
    keywords = extract_keywords(cleaned)
    entities = extract_entities(combined)
    return {
        "original_text": combined,
        "cleaned_text": cleaned,
        "keywords": keywords,
        "entities": entities,
        "char_count": len(cleaned),
        "word_count": len(cleaned.split()),
    }

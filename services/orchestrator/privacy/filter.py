"""
TELOS Privacy Filter — pre-egress PII masking and field redaction.

Applied before every outbound LLM call. Detects and masks:
- SSNs, emails, phone numbers, credit card numbers
- Password fields from UIA (marked with is_password)
- Configurable custom patterns

All masking is logged with counts for the privacy dashboard.
"""

from __future__ import annotations

import re
import logging
from dataclasses import dataclass, field

logger = logging.getLogger("telos.privacy")

# Compiled PII detection patterns
_PII_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("ssn", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("email", re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Z|a-z]{2,}\b")),
    ("phone", re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")),
    ("credit_card", re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b")),
]

_PASSWORD_MASK = "***MASKED***"
_PII_MASK = "[REDACTED]"


@dataclass
class FilterResult:
    """Outcome of a privacy filtering pass."""
    filtered_text: str
    fields_masked: int = 0
    pii_blocked: int = 0
    categories: dict[str, int] = field(default_factory=dict)


def mask_password_fields(text: str) -> tuple[str, int]:
    """Replace any value marked as a password with the standard mask.

    Password fields from UIA are wrapped as [PASSWORD:value] by the
    UIGraph extractor. This replaces them with ***MASKED***.
    """
    pattern = re.compile(r"\[PASSWORD:[^\]]*\]")
    result, count = pattern.subn(_PASSWORD_MASK, text)
    return result, count


def mask_pii(text: str) -> tuple[str, int, dict[str, int]]:
    """Detect and mask PII patterns. Returns text, total count, per-category counts."""
    total = 0
    categories: dict[str, int] = {}
    for name, pattern in _PII_PATTERNS:
        matches = pattern.findall(text)
        if matches:
            count = len(matches)
            total += count
            categories[name] = count
            text = pattern.sub(_PII_MASK, text)
    return text, total, categories


def filter_for_egress(text: str) -> FilterResult:
    """Full privacy filter pipeline applied before any outbound LLM call.

    1. Mask password fields
    2. Mask PII patterns
    3. Return metrics for the privacy dashboard
    """
    text, pw_count = mask_password_fields(text)
    text, pii_count, categories = mask_pii(text)

    if pw_count or pii_count:
        logger.info(
            "Privacy filter: masked %d password fields, %d PII instances %s",
            pw_count, pii_count, categories,
        )

    return FilterResult(
        filtered_text=text,
        fields_masked=pw_count,
        pii_blocked=pii_count,
        categories=categories,
    )

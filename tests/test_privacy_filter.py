"""
TELOS Tests — Privacy Filter test suite.

Tests PII detection, password masking, and pre-egress filtering.
"""

import pytest
from services.orchestrator.privacy.filter import (
    mask_password_fields,
    mask_pii,
    filter_for_egress,
    FilterResult,
)


class TestPasswordMasking:
    def test_masks_password_field(self):
        text = "Login: admin [PASSWORD:S3cret!] done"
        result, count = mask_password_fields(text)
        assert "S3cret!" not in result
        assert "***MASKED***" in result
        assert count == 1

    def test_masks_multiple_passwords(self):
        text = "[PASSWORD:abc] and [PASSWORD:xyz]"
        result, count = mask_password_fields(text)
        assert count == 2
        assert "abc" not in result
        assert "xyz" not in result

    def test_no_password_fields(self):
        text = "No passwords here"
        result, count = mask_password_fields(text)
        assert result == text
        assert count == 0


class TestPIIMasking:
    def test_masks_ssn(self):
        text = "SSN: 123-45-6789"
        result, count, cats = mask_pii(text)
        assert "123-45-6789" not in result
        assert "[REDACTED]" in result
        assert count == 1
        assert cats.get("ssn", 0) == 1

    def test_masks_email(self):
        text = "Contact: user@example.com"
        result, count, cats = mask_pii(text)
        assert "user@example.com" not in result
        assert count == 1
        assert "email" in cats

    def test_masks_phone(self):
        text = "Call 555-123-4567"
        result, count, cats = mask_pii(text)
        assert "555-123-4567" not in result
        assert count == 1
        assert "phone" in cats

    def test_masks_credit_card(self):
        text = "Card: 4111-1111-1111-1111"
        result, count, cats = mask_pii(text)
        assert "4111-1111-1111-1111" not in result
        assert count == 1
        assert "credit_card" in cats

    def test_masks_multiple_pii_types(self):
        text = "SSN: 123-45-6789, email: a@b.com, phone: 555-123-4567"
        result, count, cats = mask_pii(text)
        assert count >= 3
        assert "123-45-6789" not in result
        assert "a@b.com" not in result
        assert "555-123-4567" not in result

    def test_clean_text_unchanged(self):
        text = "Q1 sales total is $1,234,567"
        result, count, cats = mask_pii(text)
        assert result == text
        assert count == 0


class TestFilterForEgress:
    def test_full_pipeline(self):
        text = "User [PASSWORD:secret123] has SSN 123-45-6789 and email user@test.com"
        result = filter_for_egress(text)
        assert isinstance(result, FilterResult)
        assert "secret123" not in result.filtered_text
        assert "123-45-6789" not in result.filtered_text
        assert "user@test.com" not in result.filtered_text
        assert result.fields_masked == 1
        assert result.pii_blocked >= 2

    def test_clean_text_passes_through(self):
        text = "Copy Q1 sales total from QuickBooks to Excel cell B4"
        result = filter_for_egress(text)
        assert result.filtered_text == text
        assert result.fields_masked == 0
        assert result.pii_blocked == 0

    def test_empty_text(self):
        result = filter_for_egress("")
        assert result.filtered_text == ""
        assert result.fields_masked == 0
        assert result.pii_blocked == 0

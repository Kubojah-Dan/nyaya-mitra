from app.middleware.logging import redact_pii


def test_pii_redaction_phone():
    """Verify Indian phone numbers are masked."""
    text = "Citizen contact number is 9876543210 or +91 9123456789"
    redacted = redact_pii(text)
    assert "9876543210" not in redacted
    assert "9123456789" not in redacted
    assert "[REDACTED_PHONE]" in redacted


def test_pii_redaction_aadhaar():
    """Verify 12-digit Aadhaar formats are masked."""
    text = "Aadhaar number: 1234 5678 9012 or 123456789012"
    redacted = redact_pii(text)
    assert "1234 5678 9012" not in redacted
    assert "[REDACTED_AADHAAR]" in redacted


def test_pii_redaction_pan():
    """Verify PAN card patterns are masked."""
    text = "Tax PAN number is ABCDE1234F for reference"
    redacted = redact_pii(text)
    assert "ABCDE1234F" not in redacted
    assert "[REDACTED_PAN]" in redacted


def test_pii_redaction_email():
    """Verify email addresses are masked."""
    text = "Send copy to citizen.help@example.com immediately"
    redacted = redact_pii(text)
    assert "citizen.help@example.com" not in redacted
    assert "[REDACTED_EMAIL]" in redacted

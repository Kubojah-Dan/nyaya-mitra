"""
Tests for NyayaMitra Document Outline & Navigation Router
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_outline_generation_success():
    """Verify outline generator extracts numbered headings and creates navigable section tree."""
    sample_text = (
        "1. Parties and Jurisdiction\n"
        "This matter pertains to the applicant residing in Delhi.\n\n"
        "2. Facts of the Dispute\n"
        "The applicant received an ex-parte demand notice.\n\n"
        "2.1 Background\n"
        "Initial notice was served without proper summons under BNSS.\n\n"
        "3. Relief Sought\n"
        "Setting aside of the arbitrary demand."
    )

    payload = {
        "raw_text": sample_text,
        "title": "Legal Notice Outline"
    }

    response = client.post("/api/v1/documents/outline", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["title"] == "Legal Notice Outline"
    assert data["total_sections"] >= 3
    assert len(data["sections"]) >= 3

    # Verify section 1 has stable DOM ID
    sec1 = data["sections"][0]
    assert "parties" in sec1["section_id"].lower()
    assert sec1["level"] == 1
    assert sec1["start_char"] >= 0
    assert sec1["end_char"] > sec1["start_char"]


def test_outline_empty_text_error():
    """Verify empty text produces validation error."""
    payload = {"raw_text": "   "}
    response = client.post("/api/v1/documents/outline", json=payload)
    assert response.status_code == 400

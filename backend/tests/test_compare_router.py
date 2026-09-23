"""
Tests for NyayaMitra Document Comparison Router and CompareService
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.compare_service import CompareService, DocumentCompareRequest

client = TestClient(app)


def test_compare_json_success():
    """Verify comparing two documents via JSON returns structured deltas and summary."""
    doc_a = (
        "1. Parties\n"
        "This Agreement is made between Landlord and Tenant.\n\n"
        "2. Payment Terms\n"
        "The rent shall be paid within 30 days of the due date.\n\n"
        "3. Governing Law\n"
        "This contract is governed under Section 12 of the Legal Services Authorities Act 1987."
    )
    doc_b = (
        "1. Parties\n"
        "This Agreement is made between Landlord and Tenant.\n\n"
        "2. Payment Terms\n"
        "The rent shall be paid within 15 days of the due date.\n\n"
        "4. Dispute Resolution\n"
        "Any dispute shall be referred to arbitration in New Delhi."
    )

    payload = {
        "document_a": doc_a,
        "document_b": doc_b,
        "title_a": "Original Lease",
        "title_b": "Amended Lease",
        "language": "en"
    }

    response = client.post("/api/v1/documents/compare-json", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert data["modified_count"] >= 1
    assert data["added_count"] >= 1
    assert data["removed_count"] >= 1
    assert len(data["deltas"]) >= 3

    # Check for payment modification delta
    payment_delta = next((d for d in data["deltas"] if "Payment" in d["section_a"] or "Payment" in d["section_b"]), None)
    assert payment_delta is not None
    assert payment_delta["delta_type"] == "MODIFIED"
    assert "15" in payment_delta["description"] or "30" in payment_delta["description"]

    # Check statutory citations
    assert any("Legal Services Authorities Act" in c for c in data["citations"])


def test_compare_empty_documents_error():
    """Verify empty document submission triggers validation error."""
    payload = {
        "document_a": "   ",
        "document_b": "   ",
    }
    response = client.post("/api/v1/documents/compare-json", json=payload)
    assert response.status_code == 400


def test_compare_multipart_upload_success():
    """Verify multipart file upload comparison."""
    files = {
        "file_a": ("lease_v1.txt", b"1. Payment Terms\nRent is 10000 rupees.\n"),
        "file_b": ("lease_v2.txt", b"1. Payment Terms\nRent is 12000 rupees.\n"),
    }
    data = {
        "title_a": "Lease V1",
        "title_b": "Lease V2",
        "language": "en",
    }
    response = client.post("/api/v1/documents/compare", data=data, files=files)
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True
    assert res_data["modified_count"] >= 1

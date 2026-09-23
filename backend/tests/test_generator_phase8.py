"""
Comprehensive Test Suite for Phase 8:
Controlled Document Generator ("Mera Document")
"""

from httpx import ASGITransport, AsyncClient
import pytest

from app.main import app
from app.services.document_generator import (
    MANDATORY_DISCLAIMER,
    TEMPLATES,
    DocumentGeneratorService,
)


# ==========================================
# 1. Template Registry & Validation Tests
# ==========================================

def test_template_registry_completeness():
    templates = DocumentGeneratorService.list_templates()
    assert len(templates) >= 4
    tmpl_ids = [t["template_id"] for t in templates]
    assert "RTI_APPLICATION" in tmpl_ids
    assert "CONSUMER_COMPLAINT" in tmpl_ids
    assert "LEGAL_NOTICE_CHEQUE_BOUNCE" in tmpl_ids
    assert "RENT_DISPUTE_REPLY" in tmpl_ids


def test_validate_missing_required_fields():
    # Only providing applicant_name, missing address, authority, subject, etc.
    res = DocumentGeneratorService.validate_slots("RTI_APPLICATION", {"applicant_name": "Rohan"})
    assert res["valid"] is False
    assert len(res["missing_fields"]) >= 5
    missing_names = [f["field_name"] for f in res["missing_fields"]]
    assert "public_authority_name" in missing_names
    assert "subject_matter" in missing_names
    assert "particulars_of_information" in missing_names


def test_validate_unknown_template():
    res = DocumentGeneratorService.validate_slots("NON_EXISTENT_TMPL", {})
    assert res["valid"] is False
    assert "Unknown template" in res["error"]


# ==========================================
# 2. Document Generation Unit Tests
# ==========================================

def test_generate_rti_application():
    slots = {
        "applicant_name": "Devendra Joshi",
        "applicant_address": "House 12, MG Road, Indore, MP 452001",
        "applicant_contact": "9826012345",
        "public_authority_name": "Indore Municipal Corporation",
        "public_authority_address": "Nagar Nigam Office, Indore",
        "subject_matter": "Sanctioned layout plan of Scheme No. 54",
        "particulars_of_information": "1. Copy of approved map.\n2. Inspection report of building officers.",
        "application_fee_details": "Postal Order No. 44G 998877 of Rs. 10",
        "is_bpl": False,
        "place": "Indore",
    }
    res = DocumentGeneratorService.generate_document("RTI_APPLICATION", slots)
    assert res["success"] is True
    assert res["document_id"] is not None
    assert "Right to Information Act, 2005" in res["statutory_basis"]
    md = res["markdown_content"]
    assert "SECTION 6(1) OF THE RIGHT TO INFORMATION ACT" in md
    assert "Devendra Joshi" in md
    assert "Indore Municipal Corporation" in md
    assert "Postal Order No. 44G 998877" in md
    assert MANDATORY_DISCLAIMER in md
    assert res["sha256_hash"] is not None


def test_generate_rti_application_bpl():
    slots = {
        "applicant_name": "Kishan Lal",
        "applicant_address": "Village Rampur, Dist. Sitapur, UP",
        "applicant_contact": "9811122233",
        "public_authority_name": "Gram Panchayat Rampur",
        "public_authority_address": "Block Office, Sitapur",
        "subject_matter": "MGNREGA Job Card Payment Records",
        "particulars_of_information": "1. Daily muster rolls for March 2024.",
        "is_bpl": True,
        "bpl_card_number": "BPL-UP-2024-5544",
        "place": "Sitapur",
    }
    res = DocumentGeneratorService.generate_document("RTI_APPLICATION", slots)
    assert res["success"] is True
    md = res["markdown_content"]
    assert "Below Poverty Line (BPL)" in md
    assert "BPL-UP-2024-5544" in md
    assert "Section 7(5)" in md


def test_generate_consumer_complaint():
    slots = {
        "complainant_name": "Sunita Aggarwal",
        "complainant_address": "Flat 302, Palm Heights, Noida",
        "opposite_party_name": "QuickDelivery Logistics Ltd",
        "opposite_party_address": "Okhla Phase 3, New Delhi",
        "commission_district": "Gautam Buddha Nagar",
        "transaction_date": "10-02-2024",
        "amount_paid": "Rs. 28,500/-",
        "facts_of_case": "1. Booked parcel containing laptop.\n2. Parcel lost in transit.\n3. OP refused compensation.",
        "relief_claimed": "1. Compensation of Rs. 65,000/- with 9% interest.\n2. Litigation costs of Rs. 10,000/-.",
        "place": "Noida",
    }
    res = DocumentGeneratorService.generate_document("CONSUMER_COMPLAINT", slots)
    assert res["success"] is True
    md = res["markdown_content"]
    assert "DISTRICT CONSUMER DISPUTES REDRESSAL COMMISSION" in md
    assert "GAUTAM BUDDHA NAGAR" in md
    assert "Section 35 of the Consumer Protection Act, 2019" in md
    assert "Sunita Aggarwal" in md
    assert "QuickDelivery Logistics Ltd" in md
    assert "Rs. 28,500/-" in md
    assert "VERIFICATION" in md
    assert MANDATORY_DISCLAIMER in md


def test_generate_cheque_bounce_notice():
    slots = {
        "sender_name": "Apex Hardware Traders",
        "sender_address": "22, Chandni Chowk, Delhi 110006",
        "recipient_name": "Manish Gupta",
        "recipient_address": "B-44, Model Town, Delhi 110009",
        "cheque_number": "887711",
        "cheque_date": "15-05-2024",
        "cheque_amount": "Rs. 2,75,000/- (Rupees Two Lakh Seventy Five Thousand Only)",
        "bank_name": "HDFC Bank, Model Town Branch",
        "return_memo_date": "20-05-2024",
        "return_reason": "Funds Insufficient",
        "debt_liability_details": "Issued towards purchase of building construction materials under bill #987.",
        "place": "Delhi",
    }
    res = DocumentGeneratorService.generate_document("LEGAL_NOTICE_CHEQUE_BOUNCE", slots)
    assert res["success"] is True
    md = res["markdown_content"]
    assert "SECTION 138 OF THE NEGOTIABLE INSTRUMENTS ACT" in md
    assert "887711" in md
    assert "Rs. 2,75,000/-" in md
    assert "Funds Insufficient" in md
    assert "15 (fifteen) days" in md
    assert MANDATORY_DISCLAIMER in md


def test_generate_rent_dispute_reply():
    slots = {
        "tenant_name": "Deepak Mehra",
        "tenant_address": "Shop No. 4, Commercial Market, Pune 411001",
        "landlord_name": "Vinayak Rao",
        "landlord_address": "Bunglow 10, FC Road, Pune 411004",
        "notice_reference_date": "01-08-2024",
        "monthly_rent": "Rs. 30,000/-",
        "security_deposit": "Rs. 1,80,000/-",
        "tenancy_commencement_date": "01-04-2020",
        "tenant_rebuttal_points": "1. Rent has been punctually paid via RTGS every month.\n2. Premature termination violates clause 5 of the Lease Deed.",
        "place": "Pune",
    }
    res = DocumentGeneratorService.generate_document("RENT_DISPUTE_REPLY", slots)
    assert res["success"] is True
    md = res["markdown_content"]
    assert "FORMAL REPLY TO NOTICE OF EVICTION" in md
    assert "Deepak Mehra" in md
    assert "Vinayak Rao" in md
    assert "Rs. 30,000/-" in md
    assert "Rs. 1,80,000/-" in md
    assert MANDATORY_DISCLAIMER in md


# ==========================================
# 3. Generator API End-to-End Tests
# ==========================================

@pytest.mark.asyncio
async def test_api_list_templates():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/generator/templates")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] >= 4


@pytest.mark.asyncio
async def test_api_get_template():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/generator/templates/RTI_APPLICATION")
        assert resp.status_code == 200
        assert resp.json()["template_id"] == "RTI_APPLICATION"


@pytest.mark.asyncio
async def test_api_validate_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Incomplete payload
        resp = await client.post(
            "/api/v1/generator/validate",
            json={"template_id": "CONSUMER_COMPLAINT", "slots": {}},
        )
        assert resp.status_code == 200
        assert resp.json()["valid"] is False
        assert len(resp.json()["missing_fields"]) > 0


@pytest.mark.asyncio
async def test_api_generate_and_download_flow():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        slots = {
            "applicant_name": "Anita Roy",
            "applicant_address": "Sector 62, Noida, UP",
            "applicant_contact": "9871234560",
            "public_authority_name": "Noida Authority",
            "public_authority_address": "Sector 6, Noida",
            "subject_matter": "Park Maintenance Budget Allocation",
            "particulars_of_information": "1. Annual budget for Sector 62 Park.",
            "place": "Noida",
        }
        gen_resp = await client.post(
            "/api/v1/generator/generate",
            json={"template_id": "RTI_APPLICATION", "slots": slots},
        )
        assert gen_resp.status_code == 200
        gen_data = gen_resp.json()
        assert gen_data["success"] is True
        doc_id = gen_data["document_id"]

        # Test GET generated doc
        get_resp = await client.get(f"/api/v1/generator/documents/{doc_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["document_id"] == doc_id

        # Test Download MD
        md_resp = await client.get(f"/api/v1/generator/download/{doc_id}?format=md")
        assert md_resp.status_code == 200
        assert md_resp.headers["content-type"].startswith("text/markdown")
        assert "APPLICATION UNDER SECTION 6(1)" in md_resp.text

        # Test Download TXT
        txt_resp = await client.get(f"/api/v1/generator/download/{doc_id}?format=txt")
        assert txt_resp.status_code == 200
        assert txt_resp.headers["content-type"].startswith("text/plain")
        assert "APPLICATION UNDER SECTION 6(1)" in txt_resp.text

        # Test Download HTML
        html_resp = await client.get(f"/api/v1/generator/download/{doc_id}?format=html")
        assert html_resp.status_code == 200
        assert html_resp.headers["content-type"].startswith("text/html")
        assert "<html>" in html_resp.text

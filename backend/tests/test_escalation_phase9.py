"""
Comprehensive Test Suite for Phase 9:
Human Escalation & Official Legal Aid Resource Navigator
"""

from httpx import ASGITransport, AsyncClient
import pytest

from app.main import app
from app.services.escalation_service import (
    MANDATORY_NON_REPRESENTATION_NOTICE,
    NATIONAL_HELPLINE,
    STATE_LEGAL_AID_DIRECTORY,
    EscalationService,
)


# ==========================================
# 1. Jurisdiction & Directory Unit Tests
# ==========================================

def test_jurisdiction_resolution_explicit():
    state, dist = EscalationService.resolve_jurisdiction("Delhi", "Central")
    assert state == "DELHI"
    assert dist == "CENTRAL"


def test_jurisdiction_resolution_from_raw_location():
    state, dist = EscalationService.resolve_jurisdiction(raw_location="Pune, Maharashtra")
    assert state == "MAHARASHTRA"
    assert dist == "PUNE"


def test_jurisdiction_fallback_unrecognized_district():
    # If district doesn't exist, returns state + None district
    state, dist = EscalationService.resolve_jurisdiction("Karnataka", "UnknownTaluk")
    assert state == "KARNATAKA"
    assert dist == "UNKNOWNTALUK"


def test_jurisdiction_fallback_completely_unknown():
    # Defaults safely to Delhi / National
    state, dist = EscalationService.resolve_jurisdiction("ForeignState", "UnknownDist")
    assert state == "DELHI"


def test_get_escalation_resources_with_district():
    resources = EscalationService.get_escalation_resources(state="DELHI", district="SOUTH")
    assert len(resources) >= 2
    types = [r.authority_type for r in resources]
    assert "DLSA" in types
    assert "SLSA" in types
    assert "NALSA" in types

    dlsa = [r for r in resources if r.authority_type == "DLSA"][0]
    assert "Saket" in dlsa.address
    assert dlsa.click_to_call.startswith("tel:")
    assert "maps/search" in dlsa.map_search_url


# ==========================================
# 2. Section 12 LSAA 1987 Eligibility Tests
# ==========================================

def test_eligibility_woman_or_child():
    res = EscalationService.evaluate_section_12_eligibility(is_woman_or_child=True)
    assert res.is_eligible is True
    assert any("Section 12(c)" in q for q in res.qualifying_criteria)


def test_eligibility_sc_or_st():
    res = EscalationService.evaluate_section_12_eligibility(is_sc_or_st=True)
    assert res.is_eligible is True
    assert any("Section 12(a)" in q for q in res.qualifying_criteria)


def test_eligibility_custody():
    res = EscalationService.evaluate_section_12_eligibility(is_in_custody=True)
    assert res.is_eligible is True
    assert any("Section 12(g)" in q for q in res.qualifying_criteria)


def test_eligibility_low_income_under_ceiling():
    res = EscalationService.evaluate_section_12_eligibility(state="MAHARASHTRA", annual_income=150000)
    assert res.is_eligible is True
    assert any("ceiling" in q.lower() for q in res.qualifying_criteria)


def test_eligibility_high_income_not_qualifying():
    res = EscalationService.evaluate_section_12_eligibility(
        state="DELHI", annual_income=800000, is_woman_or_child=False
    )
    assert res.is_eligible is False
    assert len(res.qualifying_criteria) == 0


# ==========================================
# 3. Emergency Trigger Detection Tests
# ==========================================

def test_trigger_police_arrest_critical():
    needed, reasons, urgency = EscalationService.detect_escalation_triggers(
        user_message="Police has arrested my brother and taken him to the thaney."
    )
    assert needed is True
    assert urgency == "CRITICAL"
    assert any("police" in r.lower() or "arrest" in r.lower() for r in reasons)


def test_trigger_domestic_violence_high():
    needed, reasons, urgency = EscalationService.detect_escalation_triggers(
        user_message="Need an immediate domestic violence protection order against in-laws."
    )
    assert needed is True
    assert urgency == "HIGH"
    assert any("domestic" in r.lower() for r in reasons)


def test_trigger_criminal_domain_default():
    needed, reasons, urgency = EscalationService.detect_escalation_triggers(
        domain="CRIMINAL", user_message="What are the procedures for anticipatory bail?"
    )
    assert needed is True
    assert urgency == "HIGH"


def test_trigger_low_rag_confidence_medium():
    needed, reasons, urgency = EscalationService.detect_escalation_triggers(
        domain="CONSUMER", rag_confidence=0.50
    )
    assert needed is True
    assert urgency == "MEDIUM"


# ==========================================
# 4. Escalation API End-to-End Tests
# ==========================================

@pytest.mark.asyncio
async def test_api_get_resources():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/escalation/resources?state=Karnataka&district=Bengaluru+Urban")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 2
        assert any(r["authority_type"] == "DLSA" for r in data)
        assert any(r["authority_type"] == "SLSA" for r in data)


@pytest.mark.asyncio
async def test_api_check_eligibility():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "state": "Uttar Pradesh",
            "is_woman_or_child": True,
            "annual_income": 120000,
        }
        resp = await client.post("/api/v1/escalation/eligibility", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_eligible"] is True
        assert len(data["qualifying_criteria"]) >= 2


@pytest.mark.asyncio
async def test_api_recommend_escalation():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "state": "Maharashtra",
            "district": "Pune",
            "user_message": "Police is threatening to put me in lockup without FIR",
            "domain": "CRIMINAL",
            "user_profile": {"is_woman_or_child": False, "annual_income": 200000},
        }
        resp = await client.post("/api/v1/escalation/recommend", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["escalation_needed"] is True
        assert data["urgency_level"] == "CRITICAL"
        assert data["primary_contact"]["name"] == "Pune DLSA"
        assert data["primary_contact"]["click_to_call"].startswith("tel:")
        assert data["tele_law_support"]["portal_url"] == "https://www.tele-law.in"
        assert data["national_helpline"] == NATIONAL_HELPLINE
        assert "not establish an advocate-client relationship" in data["disclaimer"]


@pytest.mark.asyncio
async def test_api_helplines_directory():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/escalation/helplines")
        assert resp.status_code == 200
        data = resp.json()
        assert data["national_legal_aid_helpline"]["number"] == "15100"
        assert data["police_emergency"]["number"] == "112"
        assert data["women_helpline"]["number"] == "1091 / 181"
        assert data["supported_states_count"] >= 7

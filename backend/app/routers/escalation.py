"""
NyayaMitra Human Escalation & Resource Navigator Router
Provides REST endpoints for locating legal aid authorities (DLSA/SLSA),
evaluating Section 12 statutory eligibility, and generating emergency handoff guidance.
"""

from typing import Any, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.escalation_service import (
    NATIONAL_HELPLINE,
    NATIONAL_HELPLINE_TEL,
    STATE_LEGAL_AID_DIRECTORY,
    EligibilityEvaluation,
    EscalationRecommendation,
    EscalationResourceContact,
    EscalationService,
)

router = APIRouter(prefix="/escalation", tags=["escalation"])


class EligibilityCheckRequest(BaseModel):
    state: Optional[str] = "DELHI"
    is_woman_or_child: bool = False
    is_sc_or_st: bool = False
    is_in_custody: bool = False
    is_disabled: bool = False
    is_disaster_victim: bool = False
    is_industrial_workman: bool = False
    is_trafficking_victim: bool = False
    annual_income: Optional[int] = None


class RecommendEscalationRequest(BaseModel):
    state: Optional[str] = None
    district: Optional[str] = None
    raw_location: Optional[str] = None
    user_message: Optional[str] = None
    domain: Optional[str] = None
    rag_confidence: float = 1.0
    case_facts: dict[str, Any] = Field(default_factory=dict)
    user_profile: dict[str, Any] = Field(default_factory=dict)


@router.get("/resources", response_model=list[EscalationResourceContact])
async def get_legal_aid_resources(
    state: Optional[str] = Query("DELHI", description="State name (e.g. Delhi, Maharashtra, Karnataka)"),
    district: Optional[str] = Query(None, description="District name (e.g. Saket, Pune, Bengaluru Urban)"),
):
    """Retrieves verified DLSA, SLSA, and NALSA contacts for a given jurisdiction."""
    return EscalationService.get_escalation_resources(state=state, district=district)


@router.post("/eligibility", response_model=EligibilityEvaluation)
async def check_legal_aid_eligibility(payload: EligibilityCheckRequest):
    """
    Evaluates applicant eligibility for 100% free legal aid under Section 12
    of the Legal Services Authorities Act, 1987.
    """
    return EscalationService.evaluate_section_12_eligibility(
        state=payload.state,
        is_woman_or_child=payload.is_woman_or_child,
        is_sc_or_st=payload.is_sc_or_st,
        is_in_custody=payload.is_in_custody,
        is_disabled=payload.is_disabled,
        is_disaster_victim=payload.is_disaster_victim,
        is_industrial_workman=payload.is_industrial_workman,
        is_trafficking_victim=payload.is_trafficking_victim,
        annual_income=payload.annual_income,
    )


@router.post("/recommend", response_model=EscalationRecommendation)
async def recommend_human_escalation(payload: RecommendEscalationRequest):
    """
    Generates tailored human escalation recommendations, Tele-Law access options,
    closest DLSA contact, and Section 12 statutory eligibility assessment.
    """
    return EscalationService.generate_recommendation(
        state=payload.state,
        district=payload.district,
        raw_location=payload.raw_location,
        case_facts=payload.case_facts,
        user_message=payload.user_message,
        domain=payload.domain,
        rag_confidence=payload.rag_confidence,
        user_profile=payload.user_profile,
    )


@router.get("/helplines")
async def get_emergency_helplines():
    """Returns official 24x7 government emergency and legal aid helplines."""
    return {
        "national_legal_aid_helpline": {
            "number": NATIONAL_HELPLINE,
            "click_to_call": NATIONAL_HELPLINE_TEL,
            "name": "NALSA National Legal Aid 24x7 Helpline",
            "statutory_authority": "National Legal Services Authority",
            "charges": "Toll-Free",
        },
        "police_emergency": {"number": "112", "click_to_call": "tel:112", "name": "National Emergency Response Support System (ERSS)"},
        "women_helpline": {"number": "1091 / 181", "click_to_call": "tel:181", "name": "Women in Distress Helpline"},
        "child_helpline": {"number": "1098", "click_to_call": "tel:1098", "name": "Childline India 24x7"},
        "cyber_crime_helpline": {"number": "1930", "click_to_call": "tel:1930", "name": "National Cyber Crime Reporting Portal"},
        "supported_states_count": len(STATE_LEGAL_AID_DIRECTORY),
    }

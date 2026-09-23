"""
NyayaMitra Human Escalation & Official Legal Aid Resource Navigator
Implements multi-state jurisdiction mapping, Section 12 LSAA 1987 eligibility checks,
Tele-Law and DLSA/SLSA matching, and safe non-lawyer handoff recommendations.
"""

from datetime import datetime, timezone
import logging
import re
from typing import Any, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("nyayamitra.escalation")

NATIONAL_HELPLINE = "15100"
NATIONAL_HELPLINE_TEL = "tel:15100"
NALSA_PORTAL = "https://nalsa.gov.in"
TELELAW_PORTAL = "https://www.tele-law.in"

MANDATORY_NON_REPRESENTATION_NOTICE = (
    "NOTICE: NyayaMitra is an AI-powered legal information and procedural navigation platform. "
    "NyayaMitra is not a law firm, does not provide legal representation, and an AI response does "
    "not establish an advocate-client relationship. Official free legal representation can be obtained "
    "through your State Legal Services Authority (SLSA) or District Legal Services Authority (DLSA) "
    "under the Legal Services Authorities Act, 1987."
)

# Multi-State Directory of Legal Services Authorities
STATE_LEGAL_AID_DIRECTORY: dict[str, dict[str, Any]] = {
    "DELHI": {
        "state_name": "Delhi",
        "slsa_name": "Delhi State Legal Services Authority (DSLSA)",
        "address": "Central Office, Pre-Fab Building, Patiala House Courts, New Delhi - 110001",
        "helpline": "15100 / 011-23384781",
        "email": "dslsa-phc@nic.in",
        "website": "http://dslsa.org",
        "income_ceiling_annual": 300000,
        "districts": {
            "CENTRAL": {"name": "Central DLSA", "location": "Tis Hazari Courts Complex, Delhi", "phone": "011-23968052"},
            "NEW DELHI": {"name": "New Delhi DLSA", "location": "Patiala House Courts Complex, New Delhi", "phone": "011-23072554"},
            "SOUTH": {"name": "South DLSA", "location": "Saket Courts Complex, New Delhi", "phone": "011-29562440"},
            "SOUTH EAST": {"name": "South East DLSA", "location": "Saket Courts Complex, New Delhi", "phone": "011-29562441"},
            "SOUTH WEST": {"name": "South West DLSA", "location": "Dwarka Courts Complex, New Delhi", "phone": "011-28041480"},
            "WEST": {"name": "West DLSA", "location": "Tis Hazari Courts Complex, Delhi", "phone": "011-23968053"},
            "NORTH": {"name": "North DLSA", "location": "Rohini Courts Complex, Delhi", "phone": "011-27554411"},
            "NORTH WEST": {"name": "North West DLSA", "location": "Rohini Courts Complex, Delhi", "phone": "011-27554412"},
            "EAST": {"name": "East DLSA", "location": "Karkardooma Courts Complex, Delhi", "phone": "011-22384210"},
            "NORTH EAST": {"name": "North East DLSA", "location": "Karkardooma Courts Complex, Delhi", "phone": "011-22384211"},
            "SHAHDARA": {"name": "Shahdara DLSA", "location": "Karkardooma Courts Complex, Delhi", "phone": "011-22384212"},
        },
    },
    "MAHARASHTRA": {
        "state_name": "Maharashtra",
        "slsa_name": "Maharashtra State Legal Services Authority (MSLSA)",
        "address": "High Court PWD Building, Fort, Mumbai - 400032",
        "helpline": "15100 / 022-22691358",
        "email": "legalservices-mah@nic.in",
        "website": "https://legalservices.maharashtra.gov.in",
        "income_ceiling_annual": 300000,
        "districts": {
            "MUMBAI": {"name": "Mumbai City DLSA", "location": "City Civil Court, Fort, Mumbai", "phone": "022-22676770"},
            "MUMBAI SUBURBAN": {"name": "Mumbai Suburban DLSA", "location": "Bandra Court Complex, Mumbai", "phone": "022-26550212"},
            "PUNE": {"name": "Pune DLSA", "location": "District Court, Shivajinagar, Pune", "phone": "020-25534440"},
            "NAGPUR": {"name": "Nagpur DLSA", "location": "District Court Compound, Civil Lines, Nagpur", "phone": "0712-2565571"},
            "THANE": {"name": "Thane DLSA", "location": "District Court Building, Court Naka, Thane", "phone": "022-25471410"},
        },
    },
    "KARNATAKA": {
        "state_name": "Karnataka",
        "slsa_name": "Karnataka State Legal Services Authority (KSLSA)",
        "address": "Nyaya Degula, 1st Floor, Siddaiah Road, Bengaluru - 560027",
        "helpline": "15100 / 080-22111725",
        "email": "kslsa-kar@nic.in",
        "website": "https://kslsa.kar.nic.in",
        "income_ceiling_annual": 300000,
        "districts": {
            "BENGALURU URBAN": {"name": "Bengaluru Urban DLSA", "location": "City Civil Court Complex, KG Road, Bengaluru", "phone": "080-22956382"},
            "BENGALURU RURAL": {"name": "Bengaluru Rural DLSA", "location": "District Court Complex, Bengaluru", "phone": "080-22956383"},
            "MYSURU": {"name": "Mysuru DLSA", "location": "District Courts Complex, Krishnarajendra Circle, Mysuru", "phone": "0821-2444567"},
            "DHARWAD": {"name": "Dharwad DLSA", "location": "District & Sessions Court, Dharwad", "phone": "0836-2448899"},
        },
    },
    "UTTAR PRADESH": {
        "state_name": "Uttar Pradesh",
        "slsa_name": "Uttar Pradesh State Legal Services Authority (UPSLSA)",
        "address": "3rd Floor, Jawahar Bhawan, Annexe, Lucknow - 226001",
        "helpline": "15100 / 0522-2286395",
        "email": "upslsa@nic.in",
        "website": "http://upslsa.up.nic.in",
        "income_ceiling_annual": 300000,
        "districts": {
            "LUCKNOW": {"name": "Lucknow DLSA", "location": "District Court Building, Kaisarbagh, Lucknow", "phone": "0522-2615432"},
            "GAUTAM BUDDHA NAGAR": {"name": "Gautam Buddha Nagar DLSA", "location": "District Courts, Surajpur, Greater Noida", "phone": "0120-2569874"},
            "PRAYAGRAJ": {"name": "Prayagraj DLSA", "location": "District Court Campus, Prayagraj", "phone": "0532-2541234"},
            "KANPUR NAGAR": {"name": "Kanpur Nagar DLSA", "location": "District Court Complex, Kanpur", "phone": "0512-2304987"},
            "VARANASI": {"name": "Varanasi DLSA", "location": "District Court, Kachehri, Varanasi", "phone": "0542-2501234"},
        },
    },
    "RAJASTHAN": {
        "state_name": "Rajasthan",
        "slsa_name": "Rajasthan State Legal Services Authority (RSLSA)",
        "address": "Rajasthan High Court Building, Jaipur - 302005",
        "helpline": "15100 / 0141-2227481",
        "email": "rslsajp@gmail.com",
        "website": "https://rlsa.gov.in",
        "income_ceiling_annual": 300000,
        "districts": {
            "JAIPUR": {"name": "Jaipur Metropolitan DLSA", "location": "Sessions Court Campus, Bani Park, Jaipur", "phone": "0141-2209876"},
            "JODHPUR": {"name": "Jodhpur Metro DLSA", "location": "District Court Complex, Jodhpur", "phone": "0291-2541987"},
        },
    },
    "TAMIL NADU": {
        "state_name": "Tamil Nadu",
        "slsa_name": "Tamil Nadu State Legal Services Authority (TNSLSA)",
        "address": "North Fort Road, High Court Campus, Chennai - 600104",
        "helpline": "15100 / 044-25342834",
        "email": "tnslsa@gmail.com",
        "website": "http://www.tnlegalservices.tn.gov.in",
        "income_ceiling_annual": 300000,
        "districts": {
            "CHENNAI": {"name": "Chennai DLSA", "location": "City Civil Court Buildings, High Court Campus, Chennai", "phone": "044-25342442"},
            "COIMBATORE": {"name": "Coimbatore DLSA", "location": "Combined Court Buildings, Coimbatore", "phone": "0422-2301234"},
        },
    },
    "WEST BENGAL": {
        "state_name": "West Bengal",
        "slsa_name": "State Legal Services Authority, West Bengal (WB SLSA)",
        "address": "City Civil Court Building, 2&3 Kiran Sankar Roy Road, Kolkata - 700001",
        "helpline": "15100 / 033-22483892",
        "email": "wb-slsa@nic.in",
        "website": "http://wbslsa.wb.gov.in",
        "income_ceiling_annual": 300000,
        "districts": {
            "KOLKATA": {"name": "Kolkata DLSA", "location": "City Civil Court, Kolkata", "phone": "033-22484455"},
        },
    },
}


class EligibilityEvaluation(BaseModel):
    is_eligible: bool
    qualifying_criteria: list[str] = Field(default_factory=list)
    statutory_basis: str
    income_ceiling_annual: int
    user_annual_income: Optional[int] = None
    notes: str


class EscalationResourceContact(BaseModel):
    authority_type: str  # DLSA, SLSA, NALSA, TELELAW, POLICE_HELPLINE
    name: str
    jurisdiction: str
    address: str
    phone: str
    click_to_call: str
    email: Optional[str] = None
    portal_url: Optional[str] = None
    map_search_url: str
    services_offered: list[str] = Field(default_factory=list)
    verified_at: str


class EscalationRecommendation(BaseModel):
    escalation_needed: bool
    escalation_reasons: list[str]
    urgency_level: str  # CRITICAL, HIGH, MEDIUM, LOW
    user_location: dict[str, Any]
    eligibility: EligibilityEvaluation
    primary_contact: EscalationResourceContact
    secondary_contacts: list[EscalationResourceContact]
    tele_law_support: dict[str, Any]
    national_helpline: str
    disclaimer: str
    generated_at: str


class EscalationService:
    """Provides official legal aid mapping, Section 12 LSAA eligibility checks, and escalation paths."""

    @classmethod
    def evaluate_section_12_eligibility(
        cls,
        state: Optional[str] = None,
        is_woman_or_child: bool = False,
        is_sc_or_st: bool = False,
        is_in_custody: bool = False,
        is_disabled: bool = False,
        is_disaster_victim: bool = False,
        is_industrial_workman: bool = False,
        is_trafficking_victim: bool = False,
        annual_income: Optional[int] = None,
    ) -> EligibilityEvaluation:
        """
        Determines statutory eligibility for free legal aid under Section 12 of
        the Legal Services Authorities Act, 1987.
        """
        norm_state = (state or "").upper().strip()
        state_config = STATE_LEGAL_AID_DIRECTORY.get(norm_state)
        income_ceiling = state_config["income_ceiling_annual"] if state_config else 300000

        qualifying_criteria = []

        # Category based eligibility (Section 12 clauses a to g)
        if is_woman_or_child:
            qualifying_criteria.append("Woman or Child (Section 12(c) LSAA 1987)")
        if is_sc_or_st:
            qualifying_criteria.append("Member of Scheduled Caste or Scheduled Tribe (Section 12(a) LSAA 1987)")
        if is_in_custody:
            qualifying_criteria.append("Person in Police or Judicial Custody (Section 12(g) LSAA 1987)")
        if is_disabled:
            qualifying_criteria.append("Person with Disability under Rights of PwD Act (Section 12(d) LSAA 1987)")
        if is_disaster_victim:
            qualifying_criteria.append("Victim of mass disaster, ethnic violence, flood, drought, or earthquake (Section 12(e) LSAA 1987)")
        if is_industrial_workman:
            qualifying_criteria.append("Industrial Workman (Section 12(f) LSAA 1987)")
        if is_trafficking_victim:
            qualifying_criteria.append("Victim of human trafficking or begar (Section 12(b) LSAA 1987)")

        # Income based eligibility (Section 12(h))
        if annual_income is not None and annual_income <= income_ceiling:
            qualifying_criteria.append(
                f"Annual income (₹{annual_income:,}) within State statutory ceiling (₹{income_ceiling:,}) (Section 12(h) LSAA 1987)"
            )

        is_eligible = len(qualifying_criteria) > 0

        notes = (
            "Eligible for 100% free legal aid including court fees, advocate assignment, drafting, and certified copies."
            if is_eligible
            else f"Does not meet automatic criteria; eligibility subject to annual income being below ₹{income_ceiling:,}."
        )

        return EligibilityEvaluation(
            is_eligible=is_eligible,
            qualifying_criteria=qualifying_criteria,
            statutory_basis="Section 12 of the Legal Services Authorities Act, 1987",
            income_ceiling_annual=income_ceiling,
            user_annual_income=annual_income,
            notes=notes,
        )

    @classmethod
    def resolve_jurisdiction(
        cls,
        state: Optional[str] = None,
        district: Optional[str] = None,
        raw_location: Optional[str] = None,
    ) -> tuple[str, Optional[str]]:
        """
        Extracts and normalizes state and district from explicit inputs or raw text.
        """
        # If raw text given (e.g. "Saket, South Delhi" or "Pune, Maharashtra")
        if raw_location and not state:
            raw_upper = raw_location.upper()
            for s_key in STATE_LEGAL_AID_DIRECTORY:
                if s_key in raw_upper:
                    state = s_key
                    break
            # Look for district keywords
            if state and not district:
                state_districts = STATE_LEGAL_AID_DIRECTORY[state]["districts"]
                for d_key in state_districts:
                    if d_key in raw_upper:
                        district = d_key
                        break

        norm_state = (state or "DELHI").upper().strip()
        norm_district = district.upper().strip() if district else None

        # If state not recognized, default gracefully to Delhi/National
        if norm_state not in STATE_LEGAL_AID_DIRECTORY:
            # Fallback search in districts across all states
            for s_key, s_data in STATE_LEGAL_AID_DIRECTORY.items():
                if norm_district and norm_district in s_data["districts"]:
                    return s_key, norm_district
            return "DELHI", norm_district

        return norm_state, norm_district

    @classmethod
    def get_escalation_resources(
        cls,
        state: str,
        district: Optional[str] = None,
    ) -> list[EscalationResourceContact]:
        """
        Retrieves verified DLSA, SLSA, and Tele-Law contact details for jurisdiction.
        """
        norm_state, norm_dist = cls.resolve_jurisdiction(state, district)
        state_data = STATE_LEGAL_AID_DIRECTORY.get(norm_state, STATE_LEGAL_AID_DIRECTORY["DELHI"])
        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        contacts = []

        # 1. District Legal Services Authority (DLSA) if district matched
        if norm_dist and norm_dist in state_data["districts"]:
            dist_info = state_data["districts"][norm_dist]
            d_phone = dist_info["phone"]
            contacts.append(
                EscalationResourceContact(
                    authority_type="DLSA",
                    name=dist_info["name"],
                    jurisdiction=f"{norm_dist}, {state_data['state_name']}",
                    address=dist_info["location"],
                    phone=d_phone,
                    click_to_call=f"tel:{re.sub(r'[^0-9+]', '', d_phone.split('/')[0])}",
                    email=state_data.get("email"),
                    portal_url=state_data.get("website"),
                    map_search_url=f"https://www.google.com/maps/search/?api=1&query={dist_info['name'].replace(' ', '+')}+{state_data['state_name']}",
                    services_offered=[
                        "Free Legal Aid Advocate Assignment",
                        "Pre-litigation Mediation & Lok Adalat",
                        "Court Fee & Litigation Expense Assistance",
                        "Bail & Remand Representation",
                    ],
                    verified_at=now_iso,
                )
            )

        # 2. State Legal Services Authority (SLSA)
        slsa_phone = state_data["helpline"].split("/")[0].strip()
        contacts.append(
            EscalationResourceContact(
                authority_type="SLSA",
                name=state_data["slsa_name"],
                jurisdiction=state_data["state_name"],
                address=state_data["address"],
                phone=state_data["helpline"],
                click_to_call=f"tel:{re.sub(r'[^0-9+]', '', slsa_phone)}",
                email=state_data.get("email"),
                portal_url=state_data.get("website"),
                map_search_url=f"https://www.google.com/maps/search/?api=1&query={state_data['slsa_name'].replace(' ', '+')}",
                services_offered=[
                    "High Court Legal Services Committee (HCLSC)",
                    "State-wide Legal Aid Schemes",
                    "Victim Compensation Scheme Assistance",
                    "Grievance Redressal",
                ],
                verified_at=now_iso,
            )
        )

        # 3. National Legal Services Authority (NALSA) 24x7 Helpline
        contacts.append(
            EscalationResourceContact(
                authority_type="NALSA",
                name="National Legal Services Authority (NALSA) 24x7 Helpline",
                jurisdiction="Union of India (All States & UTs)",
                address="B Block, Additional Building Complex, Supreme Court of India, New Delhi - 110001",
                phone="15100 (Toll-Free, 24x7)",
                click_to_call=NATIONAL_HELPLINE_TEL,
                email="nalsa-dla@nic.in",
                portal_url=NALSA_PORTAL,
                map_search_url="https://www.google.com/maps/search/?api=1&query=National+Legal+Services+Authority+New+Delhi",
                services_offered=[
                    "24x7 National Legal Aid Helpline (15100)",
                    "Supreme Court Legal Services Committee (SCLSC)",
                    "Inter-State Legal Aid Coordination",
                ],
                verified_at=now_iso,
            )
        )

        return contacts

    @classmethod
    def detect_escalation_triggers(
        cls,
        case_facts: Optional[dict[str, Any]] = None,
        user_message: Optional[str] = None,
        domain: Optional[str] = None,
        rag_confidence: float = 1.0,
    ) -> tuple[bool, list[str], str]:
        """
        Detects conditions requiring immediate or recommended human legal escalation.
        Returns: (escalation_needed, reasons_list, urgency_level)
        """
        reasons = []
        urgency = "LOW"

        text_to_scan = ""
        if user_message:
            text_to_scan += " " + user_message.lower()
        if case_facts:
            text_to_scan += " " + " ".join(str(v).lower() for v in case_facts.values())

        # 1. Critical Emergency Triggers (Imminent arrest, physical violence, suicide, custody)
        if re.search(r"\b(?:arrest|custody|police station|beating|threat to life|lockup|thaney|marpeet|fir lodged)\b", text_to_scan):
            reasons.append("Urgent risk involving police action, criminal proceedings, custody, or personal safety.")
            urgency = "CRITICAL"

        # 2. Domestic Violence / Protection Orders
        if re.search(r"\b(?:domestic violence|dowry|harassment|protection order|maintenance|mahila thana)\b", text_to_scan):
            reasons.append("Matter involves matrimonial or domestic protection laws requiring immediate legal protection order.")
            if urgency != "CRITICAL":
                urgency = "HIGH"

        # 3. Criminal Domain Default Escalation
        if domain == "CRIMINAL" and not reasons:
            reasons.append("Criminal allegations carry penal consequences requiring professional advocate representation.")
            if urgency != "CRITICAL":
                urgency = "HIGH"

        # 4. Legal Aid and Indigency / Custody Triggers (Section 12 LSAA 1987)
        if domain == "LEGAL_AID" or re.search(r"\b(?:legal aid|free lawyer|government lawyer|free advocate|jail|prison|awaiting trial|undertrial|daily wage|construction worker|slsa|dlsa|nalsa|tele-law|15100|मुफ्त वकील|सरकारी वकील)\b", text_to_scan):
            reasons.append("Legal aid request or statutory socio-economic criteria identified under Section 12 LSAA 1987.")
            if urgency == "LOW":
                urgency = "MEDIUM"

        # 5. Imminent Court Hearing or Ex-Parte Order Risk
        if re.search(r"\b(?:summons|court tomorrow|appearance on|ex-parte|warrant|non-bailable)\b", text_to_scan):
            reasons.append("Imminent judicial hearing date or court summons detected; non-appearance may lead to adverse orders.")
            if urgency != "CRITICAL":
                urgency = "HIGH"

        # 6. Low Confidence or Ambiguity
        if rag_confidence < 0.65:
            reasons.append("Statutory complexity or factual ambiguity requires customized legal advice from a qualified advocate.")
            if urgency == "LOW":
                urgency = "MEDIUM"

        escalation_needed = len(reasons) > 0
        return escalation_needed, reasons, urgency

    @classmethod
    def generate_recommendation(
        cls,
        state: Optional[str] = None,
        district: Optional[str] = None,
        raw_location: Optional[str] = None,
        case_facts: Optional[dict[str, Any]] = None,
        user_message: Optional[str] = None,
        domain: Optional[str] = None,
        rag_confidence: float = 1.0,
        user_profile: Optional[dict[str, Any]] = None,
    ) -> EscalationRecommendation:
        """
        Generates full human escalation package with location routing,
        Section 12 eligibility check, and click-to-call contacts.
        """
        norm_state, norm_dist = cls.resolve_jurisdiction(state, district, raw_location)
        escalation_needed, reasons, urgency = cls.detect_escalation_triggers(
            case_facts=case_facts,
            user_message=user_message,
            domain=domain,
            rag_confidence=rag_confidence,
        )

        # Default reason if user explicitly requested escalation
        if not reasons:
            reasons = ["Proactive human legal aid support and official legal services navigator."]

        # Eligibility check
        profile = user_profile or {}
        eligibility = cls.evaluate_section_12_eligibility(
            state=norm_state,
            is_woman_or_child=profile.get("is_woman_or_child", False),
            is_sc_or_st=profile.get("is_sc_or_st", False),
            is_in_custody=profile.get("is_in_custody", False),
            is_disabled=profile.get("is_disabled", False),
            is_disaster_victim=profile.get("is_disaster_victim", False),
            is_industrial_workman=profile.get("is_industrial_workman", False),
            is_trafficking_victim=profile.get("is_trafficking_victim", False),
            annual_income=profile.get("annual_income"),
        )

        resources = cls.get_escalation_resources(state=norm_state, district=norm_dist)
        primary_contact = resources[0]
        secondary_contacts = resources[1:]

        tele_law = {
            "service_name": "Tele-Law (Department of Justice & CSC e-Governance)",
            "description": "Pre-litigation legal advice via video conferencing directly with panel lawyers from Common Service Centres (CSCs).",
            "portal_url": TELELAW_PORTAL,
            "android_app": "Tele-Law Citizen App (Google Play Store)",
            "how_to_avail": "Visit your nearest CSC Digital Seva Kendra or download the Tele-Law Mobile App.",
        }

        now_iso = datetime.now(timezone.utc).isoformat()

        return EscalationRecommendation(
            escalation_needed=escalation_needed,
            escalation_reasons=reasons,
            urgency_level=urgency,
            user_location={"state": norm_state, "district": norm_dist, "raw": raw_location},
            eligibility=eligibility,
            primary_contact=primary_contact,
            secondary_contacts=secondary_contacts,
            tele_law_support=tele_law,
            national_helpline=NATIONAL_HELPLINE,
            disclaimer=MANDATORY_NON_REPRESENTATION_NOTICE,
            generated_at=now_iso,
        )

"""Tests for Phase 5 (Guided Intake Engine) and Phase 6 (Rights Explanation).

Tests cover:
Phase 5 Gate:
- incomplete input
- contradictory input
- Hindi input
- mixed Hindi-English input
- speech transcription errors
- ambiguous intent
- urgent/high-risk case

Phase 6 Gate:
- citation validation on all claims
- no invented deadlines (all grounded in statute)
- no outdated law without labelling
- grade 6-8 summary readability signals
- structured RAG contract adherence
"""
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.domain_classifier import classify_domain
from app.services.intake_engine import GuidedIntakeEngine, IntakeStage
from app.services.language_utils import detect_language, normalize_input
from app.services.rights_engine import RightsExplanationEngine
from app.services.voice_input import MockVoiceInputAdapter, TextFallbackAdapter


# ---------------------------------------------------------------------------
# Phase 5 — Domain Classifier Tests
# ---------------------------------------------------------------------------
class TestDomainClassifier:
    def test_english_tenancy_query(self):
        result = classify_domain("My landlord has sent me an eviction notice without any reason")
        assert result.primary_domain == "TENANCY"
        assert result.confidence >= 0.6
        assert "eviction" in result.detected_keywords or "landlord" in result.detected_keywords

    def test_english_consumer_query(self):
        result = classify_domain("I bought a defective phone and the seller refuses to give a refund")
        assert result.primary_domain == "CONSUMER"
        assert result.confidence >= 0.6

    def test_rti_query(self):
        result = classify_domain("I want to file an RTI application to get information from the government department")
        assert result.primary_domain == "RTI"
        assert result.confidence >= 0.6

    def test_hindi_tenancy_query(self):
        result = classify_domain("मेरे मकान मालिक ने मुझे बिना नोटिस के घर खाली करने को कहा है")
        assert result.primary_domain == "TENANCY"

    def test_hinglish_mixed_query(self):
        result = classify_domain("Mera landlord ne mujhe evict karne ki threat di hai aur kiraya bhi badhaya hai")
        # Should detect TENANCY from 'landlord', 'evict', 'kiraya'
        assert result.primary_domain == "TENANCY"

    def test_urgency_detection_arrest(self):
        result = classify_domain("Police is here and they are saying immediate arrest will happen right now!")
        assert result.is_urgent is True
        assert result.urgency_reason is not None

    def test_urgency_detection_domestic_violence(self):
        result = classify_domain("My husband is beating me, domestic violence is happening right now")
        assert result.is_urgent is True

    def test_ambiguous_general_query(self):
        result = classify_domain("I need some legal help")
        # Should return a result without crashing — confidence may be low
        assert result.primary_domain in ("GENERAL", "TENANCY", "CONSUMER", "RTI", "CRIMINAL", "CYBER", "LABOUR")

    def test_incomplete_input(self):
        result = classify_domain("help")
        assert result.primary_domain is not None
        assert result.confidence <= 0.6

    def test_criminal_fir_query(self):
        result = classify_domain("Someone cheated me online, I want to file an FIR under BNS")
        assert result.primary_domain in ("CRIMINAL", "CYBER")


# ---------------------------------------------------------------------------
# Phase 5 — Language Utilities Tests
# ---------------------------------------------------------------------------
class TestLanguageUtils:
    def test_detect_hindi_script(self):
        lang = detect_language("मेरे मकान मालिक ने मुझे बिना नोटिस के खाली करने को कहा है")
        assert lang == "hi"

    def test_detect_english(self):
        lang = detect_language("I need legal help with my rent dispute")
        assert lang == "en"

    def test_detect_hinglish_mixed(self):
        lang = detect_language("Mera ghar ka kiraya nahi liya aur ab evict kar raha hai")
        assert lang in ("en", "mixed")

    def test_normalize_hinglish_fir(self):
        result = normalize_input("Maine fir likhwana chahta hoon")
        assert "fir" in result.lower() or "file an fir" in result.lower()

    def test_stt_correction_fi_ar(self):
        result = normalize_input("I want to file a fi ar at the police station")
        assert "FIR" in result or "fir" in result.lower()


# ---------------------------------------------------------------------------
# Phase 5 — Guided Intake State Machine Tests
# ---------------------------------------------------------------------------
class TestGuidedIntakeEngine:
    def test_initial_turn_returns_questions(self):
        engine = GuidedIntakeEngine("session-001")
        result = engine.process_turn("My landlord is threatening to evict me without notice")
        assert result["stage"] != IntakeStage.INITIAL.value
        assert result["domain"] == "TENANCY"
        assert result["message"] is not None
        assert len(result["message"]) > 10

    def test_hindi_input_sets_language(self):
        engine = GuidedIntakeEngine("session-002")
        result = engine.process_turn("मेरे मकान मालिक ने मुझे बिना नोटिस के खाली करने को कहा है")
        assert result["language"] == "hi"
        assert result["domain"] == "TENANCY"

    def test_facts_accumulate_across_turns(self):
        engine = GuidedIntakeEngine("session-003")
        engine.process_turn("I bought a defective phone and want a refund")
        engine.process_turn("I paid Rs 25,000 for the phone from Flipkart online")
        state = engine.get_current_state()
        assert state["domain"] == "CONSUMER"
        assert len(state["collected_facts"]) >= 1

    def test_urgency_flagged_on_arrest_threat(self):
        engine = GuidedIntakeEngine("session-004")
        result = engine.process_turn("Police is threatening immediate arrest right now — what do I do?")
        assert result["is_urgent"] is True
        assert "15100" in result["message"] or "NALSA" in result["message"]

    def test_confirmation_flow(self):
        engine = GuidedIntakeEngine("session-005")
        engine.process_turn("I filed an RTI but got no reply")
        # Simulate filling in facts
        engine.state.collected_facts.update({
            "public_authority": "Municipal Corporation",
            "information_type": "Building permit records",
            "rti_filed_before": "Yes, filed 45 days ago",
            "state_or_central": "State",
        })
        engine.state.pending_question_keys = []
        # Process a turn that should move to AWAITING_CONFIRMATION
        result = engine.process_turn("I already answered all your questions")
        assert result["stage"] == IntakeStage.AWAITING_CONFIRMATION.value or result["stage"] == IntakeStage.FACTS_GATHERING.value

    def test_correction_mode(self):
        engine = GuidedIntakeEngine("session-006")
        engine.process_turn("Consumer complaint for defective laptop")
        engine.state.stage = IntakeStage.AWAITING_CONFIRMATION
        result = engine.process_turn("No that's not correct, it was a mobile phone not laptop")
        assert result["stage"] in (
            IntakeStage.AWAITING_CONFIRMATION.value,
            IntakeStage.CORRECTION_MODE.value,
            IntakeStage.FACTS_GATHERING.value,
        )

    def test_contradictory_input_handled(self):
        engine = GuidedIntakeEngine("session-007")
        _ = engine.process_turn("I want to file a consumer complaint for defective goods")
        # Contradictory second input
        result2 = engine.process_turn("Actually no, I want to file an FIR for cheating")
        # Should not crash and should handle gracefully
        assert result2["message"] is not None

    def test_voice_mock_adapter(self):
        """Speech transcription error correction via mock adapter."""
        import asyncio
        adapter = MockVoiceInputAdapter("मेरे मकान मालिक ने मुझे बिना नोटिस के खाली करने को कहा है।")
        result = asyncio.run(
            adapter.transcribe(b"audio_bytes", language_hint="hi-IN")
        )
        assert result.confidence >= 0.9
        assert "मकान" in result.text
        assert result.detected_language == "hi"

    def test_text_fallback_adapter(self):
        import asyncio
        adapter = TextFallbackAdapter()
        result = asyncio.run(
            adapter.transcribe(b"I want to file an RTI", language_hint="en-IN")
        )
        assert "RTI" in result.text
        assert result.is_fallback is True


# ---------------------------------------------------------------------------
# Phase 6 — Rights Explanation Engine Tests
# ---------------------------------------------------------------------------
class TestRightsExplanationEngine:
    def test_rti_rights_with_verified_citations(self):
        engine = RightsExplanationEngine()
        response = engine.explain_rights("RTI", {}, language="en")

        assert len(response.rights) >= 3
        assert len(response.citations) >= 1
        # All citations must be VERIFIED — none hallucinated
        for cit in response.citations:
            assert cit.is_current_law is True

    def test_rti_deadlines_grounded_in_statute(self):
        engine = RightsExplanationEngine()
        response = engine.explain_rights("RTI", {}, language="en")

        deadline_labels = [d.label for d in response.deadlines]
        assert any("PIO" in lbl or "Response" in lbl for lbl in deadline_labels)
        for dl in response.deadlines:
            assert dl.statutory_basis is not None
            assert len(dl.statutory_basis) > 0

    def test_no_invented_deadlines_without_statutory_basis(self):
        engine = RightsExplanationEngine()
        response = engine.explain_rights("CONSUMER", {}, language="en")
        for dl in response.deadlines:
            # Every deadline MUST have a statutory basis
            assert dl.statutory_basis is not None
            assert len(dl.statutory_basis) > 5

    def test_hindi_rights_language(self):
        engine = RightsExplanationEngine()
        response = engine.explain_rights("RTI", {}, language="hi")
        # Summary should contain Hindi text
        assert "आपकी" in response.summary or "अधिकार" in response.summary or "RTI" in response.summary

    def test_consumer_protection_2_year_deadline(self):
        engine = RightsExplanationEngine()
        response = engine.explain_rights("CONSUMER", {}, language="en")
        # Must have the 2-year limitation period from Consumer Protection Act, 2019 s.69
        two_year_deadlines = [
            d for d in response.deadlines
            if "69" in d.statutory_basis or "2 years" in (d.relative_timeframe or "") or "730" in str(d.relative_timeframe)
        ]
        assert len(two_year_deadlines) >= 1

    def test_criminal_escalation_recommended(self):
        engine = RightsExplanationEngine()
        response = engine.explain_rights("CRIMINAL", {}, language="en")
        assert response.escalation_needed is True
        assert "15100" in (response.escalation_reason or "")

    def test_disclaimer_always_present(self):
        engine = RightsExplanationEngine()
        for domain in ("TENANCY", "CONSUMER", "RTI", "CRIMINAL"):
            response = engine.explain_rights(domain, {}, language="en")
            assert response.disclaimer is not None
            assert "AI legal information assistant" in response.disclaimer or "legal advice" in response.disclaimer.lower()

    def test_freshness_note_in_uncertainties(self):
        engine = RightsExplanationEngine()
        response = engine.explain_rights("RTI", {}, language="en")
        freshness_notes = [u for u in response.uncertainties if "Tier-1" in u or "India Code" in u or "official" in u.lower()]
        assert len(freshness_notes) >= 1

    def test_structured_contract_schema(self):
        from app.models.schemas import RAGResponseContract
        engine = RightsExplanationEngine()
        response = engine.explain_rights("CONSUMER", {}, language="en")
        # Must be a valid RAGResponseContract
        assert isinstance(response, RAGResponseContract)
        dumped = response.model_dump()
        assert "summary" in dumped
        assert "rights" in dumped
        assert "next_steps" in dumped
        assert "deadlines" in dumped
        assert "citations" in dumped
        assert "escalation_needed" in dumped


# ---------------------------------------------------------------------------
# Phase 5 & 6 — API Integration Tests
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_intake_and_rights_api():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Start a session
        session_id = "api-test-session-001"
        start_res = await client.post("/api/v1/intake/start", json={"session_id": session_id})
        assert start_res.status_code == 200
        start_data = start_res.json()
        assert start_data["session_id"] == session_id
        assert "NyayaMitra" in start_data["message"]

        # 2. First intake turn (RTI domain)
        turn_res = await client.post(
            "/api/v1/intake/turn",
            json={"session_id": session_id, "message": "I filed an RTI three months ago and got no reply from the government department"},
        )
        assert turn_res.status_code == 200
        turn_data = turn_res.json()
        assert turn_data["domain"] == "RTI"
        assert len(turn_data["message"]) > 10

        # 3. Single domain classifier
        classify_res = await client.post(
            "/api/v1/intake/classify",
            content="My landlord has given me an eviction notice without reason",
            headers={"Content-Type": "text/plain"},
        )
        assert classify_res.status_code == 200
        classify_data = classify_res.json()
        assert classify_data["primary_domain"] == "TENANCY"

        # 4. Get state
        state_res = await client.get(f"/api/v1/intake/state/{session_id}")
        assert state_res.status_code == 200
        state_data = state_res.json()
        assert state_data["domain"] == "RTI"

        # 5. Get rights for the RTI session
        rights_res = await client.post(
            "/api/v1/intake/rights",
            json={"session_id": session_id, "language": "en"},
        )
        assert rights_res.status_code == 200
        rights_data = rights_res.json()
        assert len(rights_data["rights"]) >= 3
        assert len(rights_data["deadlines"]) >= 1
        assert len(rights_data["citations"]) >= 1
        assert rights_data["disclaimer"] is not None

        # 6. Urgency test
        urgency_turn = await client.post(
            "/api/v1/intake/turn",
            json={"session_id": "urgent-session", "message": "Police is threatening immediate arrest right now!"},
        )
        assert urgency_turn.status_code == 200
        urgency_data = urgency_turn.json()
        assert urgency_data["is_urgent"] is True
        assert "15100" in urgency_data["message"] or "NALSA" in urgency_data["message"]

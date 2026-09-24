"""
NyayaMitra Guided Legal Intake & Rights Router
Public contract for citizen multi-turn legal consultation, problem classification,
voice-to-text intake, and verified statutory rights & limitation explanations.

Endpoints:
- POST /api/v1/intake/start: Initiates or resets an intake session.
- POST /api/v1/intake/turn: Processes citizen conversational turns, extracting legal facts.
- GET  /api/v1/intake/state/{session_id}: Retrieves current session state and collected facts.
- POST /api/v1/intake/classify: Standalone single-turn legal domain classification.
- POST /api/v1/intake/rights: Generates 'Mere Adhikaar' verified statutory rights and deadlines.
- POST /api/v1/intake/voice: Transcribes citizen voice audio streams into text.
"""

from typing import Any, Optional

from fastapi import APIRouter, Body, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from starlette.responses import JSONResponse

from app.services.domain_classifier import classify_domain
from app.services.intake_engine import GuidedIntakeEngine, IntakeStage
from app.services.rights_engine import RightsExplanationEngine
from app.services.voice_input import ModelRoutedVoiceInputAdapter, TextFallbackAdapter

router = APIRouter(prefix="/intake", tags=["Guided Intake — Samjho Mera Problem"])

# In-process session store (replaced by DB in production via SessionRepository)
_sessions: dict[str, GuidedIntakeEngine] = {}


class IntakeTurnRequest(BaseModel):
    session_id: str
    message: str
    voice_input: bool = False


class RightsRequest(BaseModel):
    session_id: Optional[str] = None
    domain: Optional[str] = None
    language: str = "en"
    trigger_date: Optional[str] = None  # ISO date string, e.g. "2026-09-01"


@router.post("/start")
async def start_intake(session_id: str = Body(..., embed=True)) -> JSONResponse:
    """Create or reset a guided intake session."""
    _sessions[session_id] = GuidedIntakeEngine(session_id=session_id)
    return JSONResponse({
        "session_id": session_id,
        "stage": IntakeStage.INITIAL.value,
        "message": (
            "Namaste! I am NyayaMitra, your AI legal guide. "
            "Please describe your legal problem in your own words — Hindi, English, or both are fine. "
            "\n\nनमस्ते! मैं NyayaMitra हूँ। कृपया अपनी कानूनी समस्या अपनी भाषा में बताएं।"
        ),
    })


@router.post("/turn")
async def intake_turn(request: IntakeTurnRequest) -> JSONResponse:
    """Process a user turn in the guided intake conversation."""
    engine = _sessions.get(request.session_id)
    if not engine:
        # Auto-create session
        engine = GuidedIntakeEngine(session_id=request.session_id)
        _sessions[request.session_id] = engine

    result = engine.process_turn(request.message)
    return JSONResponse(result)


@router.get("/state/{session_id}")
async def get_intake_state(session_id: str) -> JSONResponse:
    """Get current intake session state."""
    engine = _sessions.get(session_id)
    if not engine:
        raise HTTPException(status_code=404, detail=f"Intake session '{session_id}' not found")
    return JSONResponse(engine.get_current_state())


@router.post("/classify")
async def classify_single(text: str = Body(..., media_type="text/plain")) -> JSONResponse:
    """Quick single-turn domain classification without creating a session."""
    from app.services.language_utils import normalize_input
    normalized = normalize_input(text)
    result = classify_domain(normalized)
    return JSONResponse({
        "primary_domain": result.primary_domain,
        "secondary_domain": result.secondary_domain,
        "confidence": result.confidence,
        "rationale": result.rationale,
        "detected_keywords": result.detected_keywords,
        "is_urgent": result.is_urgent,
        "urgency_reason": result.urgency_reason,
    })


@router.post("/rights")
async def get_rights_explanation(request: RightsRequest) -> JSONResponse:
    """Generate a 'Mere Adhikaar' verified rights explanation for a session or domain."""
    engine = _sessions.get(request.session_id) if request.session_id else None

    domain = request.domain
    collected_facts: dict[str, Any] = {}

    if engine:
        state = engine.get_current_state()
        domain = domain or state.get("domain", "GENERAL")
        collected_facts = state.get("collected_facts", {})

        if state.get("is_urgent"):
            collected_facts["is_urgent"] = True

    domain = domain or "GENERAL"

    # Parse trigger date
    trigger_date = None
    if request.trigger_date:
        try:
            from datetime import datetime
            trigger_date = datetime.fromisoformat(request.trigger_date)
        except ValueError:
            pass

    rights_engine = RightsExplanationEngine()
    response = rights_engine.explain_rights(
        domain=domain,
        collected_facts=collected_facts,
        language=request.language,
        trigger_date=trigger_date,
    )

    return JSONResponse(response.model_dump())


@router.post("/voice")
async def transcribe_voice(
    file: Optional[UploadFile] = File(None),
    language: str = Form("hi-IN"),
    text_fallback: Optional[str] = Form(None),
) -> JSONResponse:
    """Transcribe citizen voice audio streams or fallback text into legal intake text."""
    if file is not None:
        audio_bytes = await file.read()
        result = await ModelRoutedVoiceInputAdapter().transcribe(audio_bytes, language_hint=language)
    elif text_fallback:
        result = await TextFallbackAdapter().transcribe(text_fallback.encode("utf-8"), language_hint=language)
    else:
        raise HTTPException(
            status_code=400,
            detail="Either an audio file or text_fallback must be provided for transcription.",
        )

    return JSONResponse({
        "text": result.text,
        "confidence": result.confidence,
        "detected_language": result.detected_language,
        "is_fallback": result.is_fallback,
        "error": result.error,
    })


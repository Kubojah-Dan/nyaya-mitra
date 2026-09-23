"""
NyayaMitra Legal Corpus, Citation Verification & Structural Parsing Router
Public contract for querying verified Tier-1 enactments, pinpoint statutory sections,
cross-mapping outdated provisions (IPC/CrPC/IEA -> BNS/BNSS/BSA), and parsing raw
legal sections into structured schema.

Endpoints:
- GET  /api/v1/corpus/search: Hybrid BM25 keyword and pinpoint statutory section search.
- GET  /api/v1/corpus/verify-citation: Verifies existence and validity of cited sections.
- GET  /api/v1/corpus/transition-map: Maps historical provisions to 2024 active enactments.
- POST /api/v1/corpus/parse-section: Parses raw legal text into structured section schema.
"""

from fastapi import APIRouter, Body, Query
from starlette.responses import JSONResponse

from app.services.citation_verifier import CitationVerifier
from app.services.corpus_parser import LegalCorpusParser
from app.services.retrieval import LegalRetrievalEngine
from app.services.transition_mapping import TransitionMappingService

router = APIRouter(prefix="/corpus", tags=["Legal Corpus & Citations"])


@router.get("/search")
async def search_corpus(
    q: str = Query(..., description="Query terms or section number"),
    act: str = Query(None, description="Optional act code (e.g. BNS_2023, BNSS_2023, CPA_2019, RTI_2005)"),
    limit: int = Query(5, ge=1, le=20),
):
    """Search authoritative statutory corpus with hybrid BM25 and pinpoint section matching."""
    engine = LegalRetrievalEngine()
    act_codes = [act] if act else None
    results = engine.search(query=q, act_codes=act_codes, top_k=limit)
    return JSONResponse({"count": len(results), "results": results})


@router.get("/verify-citation")
async def verify_citation(
    act: str = Query(..., description="Name or code of the Act"),
    section: str = Query(..., description="Section number to verify"),
):
    """Zero-hallucination citation verification against Tier-1 official statutes."""
    verifier = CitationVerifier()
    result = verifier.verify_citation(act_name=act, section_number=section)
    return JSONResponse(result.to_dict())


@router.get("/transition-map")
async def get_transition_map(
    act: str = Query(..., description="Old law act code (e.g. IPC, CrPC, IEA)"),
    section: str = Query(..., description="Old law section number (e.g. 420, 154, 302, 65B)"),
):
    """Get statutory transition mapping from historical law to current BNS/BNSS/BSA."""
    mapped = TransitionMappingService.map_outdated_section(act, section)
    if not mapped:
        return JSONResponse({"found": False, "message": f"No statutory transition mapping for {act} Section {section}"})
    return JSONResponse({"found": True, "mapping": mapped})


@router.post("/parse-section")
async def parse_section(
    raw_text: str = Body(..., embed=True, description="Raw statutory section text"),
    act_code: str = Body("CUSTOM", embed=True, description="Act code identifier"),
) -> JSONResponse:
    """Parse raw section string into structured statutory attributes (subsections, cognizable, bailable)."""
    parsed = LegalCorpusParser.parse_section(raw_text, act_code)
    return JSONResponse(parsed)


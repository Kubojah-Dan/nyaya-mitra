import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.citation_verifier import CitationVerifier
from app.services.corpus_parser import LegalCorpusParser
from app.services.rag_service import LegalRAGService
from app.services.retrieval import LegalRetrievalEngine
from app.services.transition_mapping import TransitionMappingService


def test_transition_mapping_ipc_to_bns():
    mapped = TransitionMappingService.map_outdated_section("IPC", "420")
    assert mapped is not None
    assert mapped["current_act"] == "Bharatiya Nyaya Sanhita, 2023"
    assert mapped["current_section"] == "318(4)"

    mapped_murder = TransitionMappingService.map_outdated_section("Indian Penal Code", "302")
    assert mapped_murder is not None
    assert mapped_murder["current_section"] == "103"

    mapped_crpc = TransitionMappingService.map_outdated_section("CrPC", "154")
    assert mapped_crpc is not None
    assert mapped_crpc["current_act"] == "Bharatiya Nagarik Suraksha Sanhita, 2023"
    assert mapped_crpc["current_section"] == "173"

    mapped_bsa = TransitionMappingService.map_outdated_section("Indian Evidence Act", "65B")
    assert mapped_bsa is not None
    assert mapped_bsa["current_act"] == "Bharatiya Sakshya Adhiniyam, 2023"
    assert mapped_bsa["current_section"] == "63"


def test_corpus_parser_and_chunking():
    raw_sample = (
        "318. Cheating. - (1) Whoever, by deceiving any person, fraudulently or dishonestly induces "
        "the person so deceived to deliver any property to any person... (2) Whoever cheats shall be punished "
        "with imprisonment for a term which may extend to three years."
    )
    parsed = LegalCorpusParser.parse_section(raw_sample, "BNS_2023")
    assert parsed["section_number"] == "318"
    assert parsed["title"] == "Cheating"
    assert len(parsed["subsections"]) >= 1

    chunks = LegalCorpusParser.chunk_section_for_retrieval(parsed)
    assert len(chunks) >= 1
    assert chunks[0]["metadata"]["act_code"] == "BNS_2023"
    assert chunks[0]["metadata"]["section_number"] == "318"


def test_citation_verifier_valid_outdated_hallucinated():
    verifier = CitationVerifier()

    # 1. Valid Tier-1 Citation
    v_valid = verifier.verify_citation("Bharatiya Nyaya Sanhita, 2023", "318")
    assert v_valid.is_valid is True
    assert v_valid.status == "VERIFIED_TIER_1"
    assert "cheating" in v_valid.verified_quote.lower()

    # 2. Outdated Citation (IPC 420)
    v_outdated = verifier.verify_citation("Indian Penal Code", "420")
    assert v_outdated.is_valid is False
    assert v_outdated.status == "OUTDATED_SUPERSEDED"
    assert "318(4)" in v_outdated.transition_note

    # 3. Hallucinated Section (Does not exist in BNS)
    v_hallucinated_sec = verifier.verify_citation("Bharatiya Nyaya Sanhita, 2023", "9999")
    assert v_hallucinated_sec.is_valid is False
    assert v_hallucinated_sec.status == "HALLUCINATED_INVALID"

    # 4. Fake Statute
    v_fake_act = verifier.verify_citation("Intergalactic Legal Code", "1")
    assert v_fake_act.is_valid is False
    assert v_fake_act.status == "HALLUCINATED_INVALID"


def test_retrieval_engine_search():
    retrieval = LegalRetrievalEngine()

    # Pinpoint section search
    results = retrieval.search("Section 173 BNSS FIR")
    assert len(results) >= 1
    assert results[0]["section_number"] == "173"
    assert "Bharatiya Nagarik Suraksha Sanhita" in results[0]["act_name"]

    # RTI query
    rti_results = retrieval.search("RTI application timeline 30 days")
    assert len(rti_results) >= 1
    assert any("Right to Information" in r["act_name"] for r in rti_results)


def test_rag_service_structured_contract():
    rag = LegalRAGService()

    # Query with outdated law reference
    response = rag.process_query("Can someone file a case against me under IPC 420 for an online trade?")
    assert response.summary is not None
    assert len(response.rights) >= 1
    assert len(response.citations) >= 1
    assert response.disclaimer is not None
    assert "AI legal information assistant" in response.disclaimer

    # Verify replacement citation is present
    has_replacement = any(c.replaces_outdated_law is not None for c in response.citations)
    assert has_replacement is True

    # Urgent query trigger test
    urgent_response = rag.process_query("The police are here threatening immediate arrest right now!")
    assert urgent_response.escalation_needed is True
    assert urgent_response.escalation_reason is not None


@pytest.mark.asyncio
async def test_corpus_and_rag_api_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Corpus search
        search_res = await client.get("/api/v1/corpus/search?q=cheating")
        assert search_res.status_code == 200
        search_data = search_res.json()
        assert search_data["count"] >= 1

        # 2. Verify citation endpoint
        verify_res = await client.get("/api/v1/corpus/verify-citation?act=BNS_2023&section=318")
        assert verify_res.status_code == 200
        verify_data = verify_res.json()
        assert verify_data["is_valid"] is True
        assert verify_data["status"] == "VERIFIED_TIER_1"

        # 3. Transition map endpoint
        trans_res = await client.get("/api/v1/corpus/transition-map?act=IPC&section=420")
        assert trans_res.status_code == 200
        trans_data = trans_res.json()
        assert trans_data["found"] is True
        assert trans_data["mapping"]["current_section"] == "318(4)"

        # 4. RAG query endpoint
        rag_res = await client.post(
            "/api/v1/rag/query",
            json={"query": "How do I file an RTI request and what is the response deadline?"},
        )
        assert rag_res.status_code == 200
        rag_data = rag_res.json()
        assert "summary" in rag_data
        assert "rights" in rag_data
        assert "deadlines" in rag_data
        assert len(rag_data["deadlines"]) >= 1
        assert "citations" in rag_data
        assert "disclaimer" in rag_data

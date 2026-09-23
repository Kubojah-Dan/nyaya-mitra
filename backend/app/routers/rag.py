from fastapi import APIRouter
from pydantic import BaseModel
from starlette.responses import JSONResponse

from app.models.schemas import RAGResponseContract
from app.services.rag_service import LegalRAGService

router = APIRouter(prefix="/rag", tags=["Citation-First RAG"])


class RAGQueryRequest(BaseModel):
    query: str
    language: str = "en"


@router.post("/query", response_model=RAGResponseContract)
async def query_legal_rag(request: RAGQueryRequest):
    """Execute citation-first RAG pipeline producing strictly validated legal assistance contract."""
    rag_service = LegalRAGService()
    response_contract = rag_service.process_query(user_query=request.query, language=request.language)
    return JSONResponse(response_contract.model_dump())

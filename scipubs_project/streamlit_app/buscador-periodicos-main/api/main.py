"""
FastAPI Backend - Hybrid Scientific Journal Recommender
Endpoint: POST /recommend
Stack: PostgreSQL + pgvector, Gemini/HF Embeddings, Groq/Gemini LLM
"""

import os
import sys
from typing import List, Optional
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db_client import get_db_client, PostgresClient
from services.hybrid_embeddings import get_embedding_service, HybridEmbeddingService
from services.openalex_client import get_openalex_client, OpenAlexClient
from services.scielo_client import get_scielo_client, SciELOClient


# Singletons carregados no startup (evita recarregar modelo a cada request)
_db_client: PostgresClient = None
_embedding_service: HybridEmbeddingService = None


app = FastAPI(
    title="SciPubs Hybrid Journal Recommender",
    description="Recomendador científico com Hybrid RAG (Dense + Sparse + Recency + Business)",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    global _db_client, _embedding_service
    print("Inicializando conexão com banco e modelo de embeddings...")
    _db_client = get_db_client()
    _embedding_service = get_embedding_service(
        provider=os.getenv("EMBEDDING_PROVIDER", "gemini"),
        gemini_api_key=os.getenv("GEMINI_API_KEY")
    )
    # Pré-carrega o modelo fastembed/sentence-transformers no startup
    if _embedding_service.provider in ("huggingface", "sentence-transformers"):
        print("Pré-carregando modelo de embeddings local (fastembed)...")
        _embedding_service.embed_text("warmup")
    print("Startup concluído.")


@app.on_event("shutdown")
def shutdown_event():
    global _db_client
    if _db_client:
        _db_client.close()


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class RecommendRequest(BaseModel):
    title: str = Field(..., min_length=5, description="Título do artigo")
    abstract: str = Field(..., min_length=50, description="Abstract do artigo")
    top_n: int = Field(default=10, ge=1, le=20)
    min_year: Optional[int] = Field(default=2021, description="Ano mínimo dos artigos considerados")
    max_apc_usd: Optional[float] = Field(default=None, description="APC máximo em USD")
    max_decision_days: Optional[int] = Field(default=None, description="Tempo máximo até primeira decisão")
    require_oa: bool = Field(default=False, description="Apenas revistas Open Access")
    generate_justifications: bool = Field(default=True, description="Gerar justificativa via LLM")


class JournalResult(BaseModel):
    journal_id: int
    title: str
    issn: Optional[str]
    semantic_score: float
    recency_score: float
    business_score: float
    match_score: float
    top_article_titles: List[str]
    top_article_years: List[int]
    justification: Optional[str]
    metadata: dict


class RecommendResponse(BaseModel):
    query_title: str
    query_abstract: str
    results: List[JournalResult]


# =============================================================================
# LLM JUSTIFICATION (ANTI-HALLUCINATION: contexto estrito do banco)
# =============================================================================

def generate_justification(
    title: str,
    abstract: str,
    journal: dict,
    articles: List[dict],
    provider: str = "gemini"
) -> Optional[str]:
    """
    Gera justificativa usando APENAS metadados e artigos do banco.
    Provider: 'gemini' ou 'groq'.
    """
    article_context = "\n".join([
        f"- {a.get('title', '')} ({a.get('pub_year', '')})" for a in articles[:5]
    ])

    prompt = f"""Você é um editor científico sênior. Com base ESTRITAMENTE nos dados do banco fornecidos abaixo, escreva uma justificativa de 2-3 frases explicando por que a revista é adequada para o artigo do usuário.

ARTIGO DO USUÁRIO:
Título: {title}
Resumo: {abstract}

REVISTA:
Título: {journal['title']}
ISSN: {journal.get('issn', 'N/A')}
Quartil JCR: {journal.get('quartil_jcr', 'N/A')}
SJR: {journal.get('sjr', 'N/A')}
Open Access: {journal.get('open_access_status', 'N/A')}
APC: {journal.get('apc_value_usd', 'N/A')} USD
Tempo médio até decisão: {journal.get('avg_days_to_first_decision', 'N/A')} dias

ARTIGOS RECENTES PUBLICADOS NESTA REVISTA (DO BANCO):
{article_context}

INSTRUÇÃO: Não invente dados. Use apenas as informações acima. Texto corrido, sem listas."""

    if provider == "groq":
        return _call_groq(prompt)
    return _call_gemini(prompt)


def _call_gemini(prompt: str) -> Optional[str]:
    import requests
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    try:
        response = requests.post(
            url,
            json={"contents": [{"parts": [{"text": prompt}]}]},
            headers={"Content-Type": "application/json"},
            timeout=20
        )
        if response.status_code == 200:
            return response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        print(f"Erro Gemini: {e}")
    return None


def _call_groq(prompt: str) -> Optional[str]:
    import requests
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama3-70b-8192",
        "messages": [
            {"role": "system", "content": "Você é um editor científico. Use apenas os dados fornecidos."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 250
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=20)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"Erro Groq: {e}")
    return None


# =============================================================================
# ENDPOINTS
# =============================================================================

@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/debug")
def debug_info():
    """Retorna informações de diagnóstico (não expõe segredos completos)."""
    import os
    return {
        "database_url_configured": bool(os.getenv("DATABASE_URL")),
        "database_url_host": os.getenv("DATABASE_URL", "").split("@")[-1].split("/")[0] if os.getenv("DATABASE_URL") else None,
        "embedding_provider": os.getenv("EMBEDDING_PROVIDER", "not set"),
        "llm_provider": os.getenv("LLM_PROVIDER", "not set"),
        "groq_key_configured": bool(os.getenv("GROQ_API_KEY")),
        "gemini_key_configured": bool(os.getenv("GEMINI_API_KEY")),
        "openalex_configured": True,
    }


# =============================================================================
# OPENALEX ENRICHMENT ENDPOINTS
# =============================================================================

class EnrichRequest(BaseModel):
    issn: Optional[str] = None
    journal_name: Optional[str] = None


class EnrichResponse(BaseModel):
    source: str
    data: dict


@app.post("/enrich/openalex", response_model=EnrichResponse)
def enrich_via_openalex(req: EnrichRequest):
    """
    Enriquece dados de uma revista via OpenAlex (h-index, citações, OA status).
    """
    try:
        client = get_openalex_client(email=os.getenv("OPENALEX_EMAIL", "scipubs@example.com"))

        if req.issn:
            result = client.get_journal_by_issn(req.issn)
        elif req.journal_name:
            result = client.get_journal_by_name(req.journal_name)
        else:
            raise HTTPException(status_code=400, detail="Informe issn ou journal_name")

        if not result:
            raise HTTPException(status_code=404, detail="Revista não encontrada no OpenAlex")

        return EnrichResponse(source="openalex", data=result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/enrich/scielo", response_model=EnrichResponse)
def enrich_via_scielo(request: EnrichRequest):
    """
    Verifica se uma revista está na SciELO.
    """
    try:
        if not request.issn:
            raise HTTPException(status_code=400, detail="Informe o ISSN")

        client = get_scielo_client()
        result = client.get_journal_by_issn(request.issn)

        if not result:
            raise HTTPException(status_code=404, detail="Revista não encontrada na SciELO")

        return EnrichResponse(source="scielo", data=result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class BatchEnrichRequest(BaseModel):
    issns: List[str]


@app.post("/enrich/batch")
def enrich_batch(req: BatchEnrichRequest):
    """
    Enriquece múltiplas revistas via OpenAlex em paralelo.
    Retorna dicionário {issn: dados_enriquecidos}.
    """
    import concurrent.futures

    client = get_openalex_client(email=os.getenv("OPENALEX_EMAIL", "scipubs@example.com"))
    results = {}

    def fetch(issn):
        try:
            data = client.get_journal_by_issn(issn)
            return issn, data
        except Exception as e:
            return issn, {"error": str(e)}

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(fetch, issn) for issn in req.issns]
        for future in concurrent.futures.as_completed(futures):
            issn, data = future.result()
            if data:
                results[issn] = data

    return {"source": "openalex", "results": results}


@app.post("/recommend", response_model=RecommendResponse)
def recommend(req: RecommendRequest):
    """
    Recomenda periódicos científicos usando Hybrid RAG.
    """
    try:
        # 1. Usa singletons inicializados no startup
        db = _db_client
        embedding_service = _embedding_service

        # 2. Gera embeddings da query (título 1.5x, abstract 1.0x)
        title_embedding = embedding_service.embed_text(req.title).tolist()
        abstract_embedding = embedding_service.embed_text(req.abstract).tolist()

        # 3. Busca híbrida + scoring no banco
        scored_journals = db.score_journals(
            title_embedding=title_embedding,
            abstract_embedding=abstract_embedding,
            query_text=f"{req.title} {req.abstract}",
            limit=req.top_n * 3,  # Pega mais candidatos para normalização mais estável
            min_year=req.min_year,
            max_apc_usd=req.max_apc_usd,
            max_decision_days=req.max_decision_days,
            require_oa=req.require_oa
        )

        if not scored_journals:
            raise HTTPException(status_code=404, detail="Nenhuma revista encontrada para os critérios.")

        # 3.1 Normaliza scores para escala 0-100 (melhor resultado = 100)
        max_match = max(sj["match_score"] for sj in scored_journals) or 1.0
        max_semantic = max(sj["semantic_score"] for sj in scored_journals) or 1.0
        max_recency = max(sj["recency_score"] for sj in scored_journals) or 1.0
        max_business = max(sj["business_score"] for sj in scored_journals) or 1.0

        for sj in scored_journals:
            sj["match_score"] = round(min((sj["match_score"] / max_match) * 100, 100.0), 1)
            sj["semantic_score"] = round(min((sj["semantic_score"] / max_semantic) * 100, 100.0), 1)
            sj["recency_score"] = round(min((sj["recency_score"] / max_recency) * 100, 100.0), 1)
            sj["business_score"] = round(min((sj["business_score"] / max_business) * 100, 100.0), 1)

        # Mantém apenas o top_n solicitado após normalização
        scored_journals = scored_journals[:req.top_n]

        # 4. Enriquece com metadados completos e gera justificativas
        results = []
        llm_provider = os.getenv("LLM_PROVIDER", "gemini")

        for sj in scored_journals:
            journal_id = sj["journal_id"]
            journal_full = db.get_journal_by_id(journal_id)
            if not journal_full:
                continue

            # Artigos relevantes desta revista para contexto da justificativa
            articles = db.get_top_articles_for_journal(
                journal_id=journal_id,
                title_embedding=title_embedding,
                abstract_embedding=abstract_embedding,
                query_text=f"{req.title} {req.abstract}",
                limit=5
            )

            justification = None
            if req.generate_justifications:
                justification = generate_justification(
                    title=req.title,
                    abstract=req.abstract,
                    journal=journal_full,
                    articles=articles,
                    provider=llm_provider
                )

            results.append(JournalResult(
                journal_id=journal_id,
                title=sj["title"],
                issn=sj["issn"],
                semantic_score=float(sj["semantic_score"]),
                recency_score=float(sj["recency_score"]),
                business_score=float(sj["business_score"]),
                match_score=float(sj["match_score"]),
                top_article_titles=sj["top_article_titles"] or [],
                top_article_years=sj["top_article_years"] or [],
                justification=justification,
                metadata=dict(journal_full)
            ))

        return RecommendResponse(
            query_title=req.title,
            query_abstract=req.abstract,
            results=results
        )

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f"Erro interno: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)
        raise HTTPException(status_code=500, detail=error_detail)

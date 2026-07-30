"""
Hybrid Scientific Matcher
Algoritmo de scoring que combina:
  - Semantic Similarity (últimos 3 anos de artigos da revista)
  - Recency Factor
  - Business Metadata (APC, OA, tempo de decisão)
  - LLM final apenas para justificativa
"""

import os
import json
import math
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import logging

from services.hybrid_embeddings import HybridEmbeddingService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class MatchResult:
    journal_id: int
    title: str
    issn: str
    semantic_score: float
    recency_score: float
    business_score: float
    match_score: float
    metadata: Dict
    justification: Optional[str] = None


class HybridScientificMatcher:
    """
    Motor de matching híbrido para recomendação de periódicos científicos.
    Sem chamadas LLM na recuperação; LLM apenas na geração de justificativa.
    """

    def __init__(
        self,
        embedding_service: HybridEmbeddingService,
        llm_provider: str = "gemini",  # 'gemini' ou 'ollama'
        llm_api_key: Optional[str] = None,
        ollama_model: str = "llama3"
    ):
        self.embedding_service = embedding_service
        self.llm_provider = llm_provider
        self.llm_api_key = llm_api_key
        self.ollama_model = ollama_model

    def rank_journals(
        self,
        query_title: str,
        query_abstract: str,
        candidate_journals: List[Dict],
        top_n: int = 10,
        max_apc_usd: Optional[float] = None,
        max_days_to_decision: Optional[int] = None,
        require_oa: bool = False,
        current_year: int = 2026
    ) -> List[MatchResult]:
        """
        Ranking híbrido das revistas candidatas.

        Args:
            query_title: Título do artigo do usuário
            query_abstract: Abstract do artigo do usuário
            candidate_journals: Lista de dicts com metadados + artigos recentes
            top_n: Quantidade de resultados finais
            max_apc_usd: Filtro hard de APC máximo
            max_days_to_decision: Filtro hard de tempo máximo
            require_oa: Se True, só aceita revistas OA
            current_year: Ano atual para cálculo de recency
        """
        query_vec = self.embedding_service.embed_query(query_title, query_abstract)
        query_terms = self.embedding_service.extract_technical_terms(f"{query_title} {query_abstract}")

        results = []

        for journal in candidate_journals:
            # Filtros hard
            apc = journal.get("apc_value_usd")
            if max_apc_usd is not None and apc is not None and apc > max_apc_usd:
                continue

            decision_days = journal.get("avg_days_to_first_decision")
            if max_days_to_decision is not None and decision_days is not None and decision_days > max_days_to_decision:
                continue

            if require_oa and journal.get("open_access_status") not in ["gold", "hybrid", "bronze"]:
                continue

            # 1. Semantic Score
            sem_score = self._compute_semantic_score(query_vec, journal)

            # 2. Recency Score
            rec_score = self._compute_recency_score(journal, current_year)

            # 3. Business Score
            biz_score = self._compute_business_score(journal)

            # 4. Match Score final (pesos configuráveis)
            match_score = (
                0.55 * sem_score +
                0.25 * rec_score +
                0.20 * biz_score
            )

            results.append(MatchResult(
                journal_id=journal.get("id", 0),
                title=journal.get("title", ""),
                issn=journal.get("issn", ""),
                semantic_score=round(sem_score, 4),
                recency_score=round(rec_score, 4),
                business_score=round(biz_score, 4),
                match_score=round(match_score, 4),
                metadata=journal
            ))

        # Ordena por match_score decrescente
        results.sort(key=lambda x: x.match_score, reverse=True)
        top_results = results[:top_n]

        # LLM final: gera justificativa para cada um dos top-N
        for r in top_results:
            r.justification = self._generate_justification(query_title, query_abstract, r)

        return top_results

    def _compute_semantic_score(self, query_vec, journal: Dict) -> float:
        """
        Calcula similaridade semântica média entre a query e artigos da revista.
        Considera artigos dos últimos 3 anos com peso maior.
        """
        import numpy as np

        articles = journal.get("recent_articles", [])
        if not articles:
            # Fallback: compara com scope_embedding da revista
            scope_vec = journal.get("scope_embedding")
            if scope_vec is not None:
                return self._cosine_sim(query_vec, np.array(scope_vec))
            return 0.0

        similarities = []
        weights = []

        for art in articles:
            art_vec = art.get("combined_embedding")
            if art_vec is None:
                continue

            sim = self._cosine_sim(query_vec, np.array(art_vec))
            year = art.get("pub_year", 2024)
            recency_weight = self._year_weight(year)

            similarities.append(sim)
            weights.append(recency_weight)

        if not similarities:
            return 0.0

        weighted_sum = sum(s * w for s, w in zip(similarities, weights))
        total_weight = sum(weights)
        return weighted_sum / total_weight if total_weight > 0 else 0.0

    def _compute_recency_score(self, journal: Dict, current_year: int) -> float:
        """
        Recency factor: recompensa revistas com publicações recentes sobre o tema.
        Usa distribuição exponencial: artigos mais recentes têm peso maior.
        """
        articles = journal.get("recent_articles", [])
        if not articles:
            return 0.5  # Neutro se não há dados

        scores = []
        for art in articles:
            year = art.get("pub_year", current_year)
            years_ago = max(0, current_year - year)
            score = math.exp(-0.3 * years_ago)
            scores.append(score)

        return sum(scores) / len(scores)

    def _compute_business_score(self, journal: Dict) -> float:
        """
        Business metadata score: APC baixo, OA favorável, decisão rápida.
        Normalizado entre 0 e 1.
        """
        score = 0.0
        weights = {"apc": 0.4, "oa": 0.35, "decision": 0.25}

        # APC (menor é melhor)
        apc = journal.get("apc_value_usd")
        if apc is not None:
            if apc == 0:
                apc_score = 1.0
            else:
                # Normaliza: $0 = 1.0, $3000 = 0.0
                apc_score = max(0.0, 1.0 - (apc / 3000.0))
            score += weights["apc"] * apc_score
        else:
            score += weights["apc"] * 0.5

        # Open Access
        oa_status = journal.get("open_access_status", "")
        oa_scores = {
            "gold": 1.0,
            "hybrid": 0.7,
            "bronze": 0.6,
            "green": 0.5,
            "subscription": 0.2
        }
        score += weights["oa"] * oa_scores.get(oa_status, 0.5)

        # Tempo médio até primeira decisão (menor é melhor)
        decision_days = journal.get("avg_days_to_first_decision")
        if decision_days is not None:
            # 0 dias = 1.0, 180 dias = 0.0
            decision_score = max(0.0, 1.0 - (decision_days / 180.0))
            score += weights["decision"] * decision_score
        else:
            score += weights["decision"] * 0.5

        return score

    def _cosine_sim(self, a, b) -> float:
        """Similaridade de cosseno entre dois vetores numpy"""
        import numpy as np
        a = np.array(a).flatten()
        b = np.array(b).flatten()
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))

    def _year_weight(self, year: int, current_year: int = 2026) -> float:
        """Peso por ano de publicação: mais recente = maior peso"""
        years_ago = max(0, current_year - year)
        if years_ago <= 1:
            return 1.0
        elif years_ago <= 2:
            return 0.8
        elif years_ago <= 3:
            return 0.6
        else:
            return 0.4

    def _generate_justification(
        self,
        query_title: str,
        query_abstract: str,
        match: MatchResult
    ) -> Optional[str]:
        """
        LLM final: gera justificativa natural de alinhamento semântico.
        Recebe metadados do top journal e gera explicação.
        """
        prompt = self._build_justification_prompt(query_title, query_abstract, match)

        if self.llm_provider == "gemini" and self.llm_api_key:
            return self._call_gemini(prompt)
        elif self.llm_provider == "ollama":
            return self._call_ollama(prompt)

        # Fallback textual
        return (
            f"{match.title} apresenta {match.semantic_score*100:.1f}% de alinhamento semântico "
            f"com seu artigo, com score de recency de {match.recency_score*100:.1f}% "
            f"e score de viabilidade editorial de {match.business_score*100:.1f}%."
        )

    def _build_justification_prompt(self, title: str, abstract: str, match: MatchResult) -> str:
        meta = match.metadata
        sample_abstracts = "\n".join([
            f"- {art.get('title', '')}" for art in meta.get("recent_articles", [])[:3]
        ])

        return f"""Você é um editor científico sênior. Explique em 2-3 frases por que a revista abaixo é um excelente match para o artigo do usuário.

ARTIGO DO USUÁRIO:
Título: {title}
Resumo: {abstract}

REVISTA RECOMENDADA:
Título: {match.title}
ISSN: {match.issn}
Quartil JCR: {meta.get('quartil_jcr', 'N/A')}
SJR: {meta.get('sjr', 'N/A')}
APC: {meta.get('apc_value_usd', 'N/A')} USD
Open Access: {meta.get('open_access_status', 'N/A')}
Tempo médio até decisão: {meta.get('avg_days_to_first_decision', 'N/A')} dias

TÍTULOS RECENTES PUBLICADOS NESTA REVISTA:
{sample_abstracts}

PONTUAÇÕES CALCULADAS:
- Alinhamento semântico: {match.semantic_score*100:.1f}%
- Fator recency: {match.recency_score*100:.1f}%
- Viabilidade editorial: {match.business_score*100:.1f}%

ESCREVA APENAS a justificativa em texto corrido, sem listas ou JSON."""

    def _call_gemini(self, prompt: str) -> Optional[str]:
        import requests
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={self.llm_api_key}"
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
            logger.warning(f"Erro ao gerar justificativa via Gemini: {e}")
        return None

    def _call_ollama(self, prompt: str) -> Optional[str]:
        try:
            import ollama
            response = ollama.generate(
                model=self.ollama_model,
                prompt=prompt,
                stream=False,
                options={"num_predict": 250, "temperature": 0.7}
            )
            return response.get("response", "")
        except Exception as e:
            logger.warning(f"Erro ao gerar justificativa via Ollama: {e}")
        return None

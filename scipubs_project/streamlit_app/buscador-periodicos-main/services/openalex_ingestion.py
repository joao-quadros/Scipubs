"""
OpenAlex Ingestion Service
Busca artigos recentes por revista e popula o schema pgvector.
OpenAlex é gratuito e não requer autenticação (rate limit: 100 req/s).
"""

import re
import time
from typing import List, Dict, Optional
import requests
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OpenAlexIngestionService:
    """Serviço para buscar artigos recentes no OpenAlex"""

    BASE_URL = "https://api.openalex.org/works"
    POLITE_EMAIL = "scipubs@example.com"

    def __init__(self, email: Optional[str] = None, requests_per_second: int = 10):
        self.email = email or self.POLITE_EMAIL
        self.delay = 1.0 / requests_per_second

    def _get(self, params: Dict) -> Dict:
        """Faz requisição GET para OpenAlex com politeness"""
        headers = {"User-Agent": f"mailto:{self.email}"}
        params["mailto"] = self.email
        response = requests.get(self.BASE_URL, params=params, headers=headers, timeout=8)
        response.raise_for_status()
        time.sleep(self.delay)
        return response.json()

    def fetch_articles_for_journal(
        self,
        journal_name: str,
        issn: Optional[str] = None,
        per_page: int = 10,
        min_year: int = 2021
    ) -> List[Dict]:
        """
        Busca artigos recentes de uma revista no OpenAlex.

        Args:
            journal_name: Nome da revista
            issn: ISSN da revista (preferencial)
            per_page: Quantidade de artigos
            min_year: Ano mínimo de publicação

        Returns:
            Lista de artigos normalizados
        """
        query_parts = []

        if issn:
            query_parts.append(f"locations.source.issn:{issn}")
        else:
            # Escapa aspas no nome da revista
            safe_name = journal_name.replace('"', '\\"')
            query_parts.append(f'locations.source.display_name:"{safe_name}"')

        query_parts.append(f"publication_year:>{min_year - 1}")
        query = ", ".join(query_parts)

        params = {
            "q": query,
            "per_page": per_page,
            "sort": "publication_date:desc",
            "filter": f"has_abstract:true"
        }

        try:
            logger.info(f"Buscando artigos OpenAlex para: {journal_name[:50]}...")
            data = self._get(params)
            results = data.get("results", [])
            logger.info(f"OpenAlex retornou {len(results)} resultados para {journal_name[:50]}...")
            return [self._normalize_article(r) for r in results]
        except Exception as e:
            logger.warning(f"Erro ao buscar artigos para {journal_name}: {e}")
            return []

    def _normalize_article(self, raw: Dict) -> Dict:
        """Normaliza artigo do OpenAlex para o schema"""
        title = raw.get("display_name", "")
        abstract = self._reconstruct_abstract(raw.get("abstract_inverted_index", {}))
        doi = raw.get("doi", "")
        year = raw.get("publication_year")
        date = raw.get("publication_date")
        citations = raw.get("cited_by_count", 0)

        return {
            "title": title,
            "abstract": abstract,
            "doi": doi or f"openalex:{raw.get('id')}",
            "pub_year": year,
            "pub_date": date,
            "citation_count": citations,
            "article_text": f"{title} {abstract}".strip()
        }

    def _reconstruct_abstract(self, inverted_index: Dict) -> str:
        """Reconstrói abstract a partir do inverted index do OpenAlex"""
        if not inverted_index:
            return ""

        # Cria lista de (palavra, posicao_inicial)
        word_positions = []
        for word, positions in inverted_index.items():
            for pos in positions:
                word_positions.append((pos, word))

        word_positions.sort(key=lambda x: x[0])
        return " ".join([w for _, w in word_positions])


def get_openalex_ingestion_service(email: Optional[str] = None) -> OpenAlexIngestionService:
    """Factory padrão"""
    return OpenAlexIngestionService(email=email)

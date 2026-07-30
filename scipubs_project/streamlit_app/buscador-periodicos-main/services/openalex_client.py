"""
OpenAlex API Client
Cliente para integração com a OpenAlex API (gratuita, sem autenticação)
Documentação: https://docs.openalex.org/
"""

import requests
import time
from typing import Dict, Optional, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OpenAlexClient:
    """Cliente para a API OpenAlex"""
    
    BASE_URL = "https://api.openalex.org"
    
    def __init__(self, email: Optional[str] = None):
        """
        Inicializa o cliente OpenAlex
        
        Args:
            email: Email opcional para politeness (recomendado pela OpenAlex)
        """
        self.email = email
        self.session = requests.Session()
        
        # Headers para identificação (politeness)
        self.headers = {
            "User-Agent": "SciPubs/1.0 (mailto:{})".format(email or "scipubs@example.com"),
            "Accept": "application/json"
        }
    
    def _make_request(self, endpoint: str, params: Dict = None, max_retries: int = 3) -> Optional[Dict]:
        """
        Faz requisição à API OpenAlex com retry
        
        Args:
            endpoint: Endpoint da API
            params: Parâmetros da query
            max_retries: Número máximo de tentativas
            
        Returns:
            Dicionário com resposta JSON ou None em caso de erro
        """
        url = f"{self.BASE_URL}{endpoint}"
        
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, params=params, headers=self.headers, timeout=10)
                
                # Rate limit handling
                if response.status_code == 429:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning(f"Rate limit hit. Waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                else:
                    logger.error(f"Max retries exceeded for endpoint: {endpoint}")
                    return None
    
    def get_journal_by_issn(self, issn: str) -> Optional[Dict]:
        """
        Busca revista por ISSN
        
        Args:
            issn: ISSN da revista (com ou sem hífen)
            
        Returns:
            Dicionário com dados da revista ou None
        """
        # Remove hífen se presente
        issn_clean = issn.replace("-", "").strip()
        
        endpoint = f"/sources/issn:{issn_clean}"
        result = self._make_request(endpoint)

        if result and result.get("id"):
            return self._normalize_journal_data(result)

        return None
    
    def get_journal_by_name(self, name: str) -> Optional[Dict]:
        """
        Busca revista por nome (search)
        
        Args:
            name: Nome da revista
            
        Returns:
            Dicionário com dados da revista ou None
        """
        params = {"search": name, "per_page": 1, "filter": "type:journal"}
        endpoint = "/sources"
        result = self._make_request(endpoint, params)
        
        if result and "results" in result and len(result["results"]) > 0:
            return self._normalize_journal_data(result["results"][0])
        
        return None
    
    def search_similar_articles(self, abstract: str, per_page: int = 5) -> List[Dict]:
        """
        Busca artigos semanticamente similares ao abstract
        
        Args:
            abstract: Abstract do artigo
            per_page: Número de resultados
            
        Returns:
            Lista de artigos similares
        """
        params = {
            "search.semantic": abstract,
            "per_page": per_page,
            "sort": "relevance_score:desc"
        }
        endpoint = "/works"
        result = self._make_request(endpoint, params)
        
        if result and "results" in result:
            return [self._normalize_article_data(article) for article in result["results"]]
        
        return []
    
    def _normalize_journal_data(self, raw_data: Dict) -> Dict:
        """
        Normaliza dados da revista para formato unificado
        
        Args:
            raw_data: Dados brutos da OpenAlex
            
        Returns:
            Dicionário normalizado
        """
        return {
            "id": raw_data.get("id"),
            "issn": raw_data.get("issn", [None])[0] if raw_data.get("issn") else None,
            "nome": raw_data.get("display_name"),
            "tipo": raw_data.get("type"),
            "h_index": raw_data.get("h_index"),
            "i10_index": raw_data.get("i10_index"),
            "works_count": raw_data.get("works_count"),
            "cited_by_count": raw_data.get("cited_by_count"),
            "2yr_mean_citedness": raw_data.get("2yr_mean_citedness"),
            "is_in_doaj": raw_data.get("is_in_doaj", False),
            "is_oa": raw_data.get("is_oa", False),
            "country": raw_data.get("country_code"),
            "publisher": raw_data.get("publisher"),
            "homepage_url": raw_data.get("homepage_url"),
            "concepts": [c.get("display_name") for c in raw_data.get("concepts", [])[:5]],
            "apc_usd": raw_data.get("apc_usd"),
            "societies": [s.get("display_name") for s in raw_data.get("societies", [])]
        }
    
    def _normalize_article_data(self, raw_data: Dict) -> Dict:
        """
        Normaliza dados de artigo para formato unificado
        
        Args:
            raw_data: Dados brutos da OpenAlex
            
        Returns:
            Dicionário normalizado
        """
        primary_location = raw_data.get("primary_location") or {}
        source = primary_location.get("source") or {}
        
        return {
            "id": raw_data.get("id"),
            "titulo": raw_data.get("title"),
            "ano": raw_data.get("publication_year"),
            "tipo": raw_data.get("type"),
            "citacao_count": raw_data.get("cited_by_count", 0),
            "revista_nome": source.get("display_name"),
            "revista_issn": source.get("issn", [None])[0] if source.get("issn") else None,
            "revista_tipo": source.get("type"),
            "doi": raw_data.get("doi"),
            "url": raw_data.get("id"),
            "concepts": [c.get("display_name") for c in raw_data.get("concepts", [])[:3]]
        }


# Singleton instance
_openalex_client = None

def get_openalex_client(email: Optional[str] = None) -> OpenAlexClient:
    """
    Retorna instância singleton do cliente OpenAlex
    
    Args:
        email: Email para politeness
        
    Returns:
        Instância de OpenAlexClient
    """
    global _openalex_client
    if _openalex_client is None:
        _openalex_client = OpenAlexClient(email)
    return _openalex_client

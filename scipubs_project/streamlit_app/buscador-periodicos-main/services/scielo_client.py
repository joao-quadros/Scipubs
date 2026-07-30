"""
SciELO ArticleMeta API Client
Cliente para integração com a API ArticleMeta do SciELO
Documentação: https://articlemeta.scielo.org/api/v1/
"""

import requests
import time
from typing import Dict, Optional, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SciELOClient:
    """Cliente para a API ArticleMeta do SciELO"""
    
    BASE_URL = "https://articlemeta.scielo.org/api/v1"
    
    def __init__(self):
        """Inicializa o cliente SciELO"""
        self.session = requests.Session()
        self.headers = {
            "Accept": "application/json",
            "User-Agent": "SciPubs/1.0"
        }
    
    def _make_request(self, endpoint: str, params: Dict = None, max_retries: int = 3) -> Optional[Dict]:
        """
        Faz requisição à API SciELO com retry
        
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
        Busca revista por ISSN na SciELO
        
        Args:
            issn: ISSN da revista (com ou sem hífen)
            
        Returns:
            Dicionário com dados da revista ou None
        """
        # Remove hífen se presente
        issn_clean = issn.replace("-", "").strip()
        
        endpoint = f"/journal/issn/{issn_clean}"
        result = self._make_request(endpoint)
        
        if result:
            return self._normalize_journal_data(result)
        
        return None
    
    def get_journal_by_collection(self, collection: str, issn: str) -> Optional[Dict]:
        """
        Busca revista por ISSN em uma coleção específica (ex: scl, br)
        
        Args:
            collection: Código da coleção (ex: 'scl' para SciELO, 'br' para Brasil)
            issn: ISSN da revista
            
        Returns:
            Dicionário com dados da revista ou None
        """
        issn_clean = issn.replace("-", "").strip()
        endpoint = f"/journal/{collection}/issn/{issn_clean}"
        result = self._make_request(endpoint)
        
        if result:
            return self._normalize_journal_data(result)
        
        return None
    
    def _normalize_journal_data(self, raw_data: Dict) -> Dict:
        """
        Normaliza dados da revista para formato unificado
        
        Args:
            raw_data: Dados brutos da SciELO
            
        Returns:
            Dicionário normalizado
        """
        return {
            "id": raw_data.get("id"),
            "issn": raw_data.get("issn", [None])[0] if raw_data.get("issn") else None,
            "nome": raw_data.get("title"),
            "colecao": raw_data.get("collection"),
            "sigla": raw_data.get("short_title"),
            "status": raw_data.get("status"),
            "url": raw_data.get("url"),
            "temas": raw_data.get("subject_areas", []),
            "linguas": raw_data.get("languages", []),
            "inicio_publicacao": raw_data.get("publishing_year_start"),
            "fim_publicacao": raw_data.get("publishing_year_end"),
            "total_issues": raw_data.get("total_issues"),
            "is_scielo": True  # Flag para identificar que é da SciELO
        }


# Singleton instance
_scielo_client = None

def get_scielo_client() -> SciELOClient:
    """
    Retorna instância singleton do cliente SciELO
    
    Returns:
        Instância de SciELOClient
    """
    global _scielo_client
    if _scielo_client is None:
        _scielo_client = SciELOClient()
    return _scielo_client

"""
Similar Articles Finder
Busca artigos semanticamente similares via OpenAlex
"""

from typing import List, Dict, Optional
import logging

from services.openalex_client import get_openalex_client
from services.cache_manager import get_cache_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimilarArticlesFinder:
    """Buscador de artigos similares via OpenAlex Semantic Search"""
    
    def __init__(self, email_openalex: Optional[str] = None):
        """
        Inicializa o buscador
        
        Args:
            email_openalex: Email para politeness OpenAlex
        """
        self.openalex_client = get_openalex_client(email_openalex)
        self.cache_manager = get_cache_manager()
    
    def find_similar_articles(
        self,
        abstract: str,
        per_page: int = 5,
        use_cache: bool = True
    ) -> List[Dict]:
        """
        Busca artigos semanticamente similares
        
        Args:
            abstract: Abstract do artigo
            per_page: Número de resultados
            use_cache: Se deve usar cache
            
        Returns:
            Lista de artigos similares
        """
        # Gera chave de cache
        cache_key = f"similar_articles:{hash(abstract)}:{per_page}"
        
        # Tenta cache primeiro
        if use_cache:
            cached = self.cache_manager.get(cache_key)
            if cached:
                logger.info("Artigos similares recuperados do cache")
                return cached
        
        # Busca na OpenAlex
        logger.info("Buscando artigos similares na OpenAlex...")
        articles = self.openalex_client.search_similar_articles(abstract, per_page)
        
        if not articles:
            logger.warning("Nenhum artigo similar encontrado")
            return []
        
        # Salva no cache (TTL: 7 dias)
        if use_cache:
            self.cache_manager.set(cache_key, articles, ttl_seconds=604800)
        
        logger.info(f"Encontrados {len(articles)} artigos similares")
        return articles
    
    def enrich_with_journal_data(
        self,
        articles: List[Dict],
        df_local: Optional = None
    ) -> List[Dict]:
        """
        Enriquece artigos com dados da revista (base local se disponível)
        
        Args:
            articles: Lista de artigos
            df_local: DataFrame local de revistas (opcional)
            
        Returns:
            Lista de artigos enriquecidos
        """
        if df_local is None:
            return articles
        
        enriched = []
        
        for article in articles:
            journal_issn = article.get("revista_issn")
            
            if journal_issn:
                # Tenta encontrar na base local
                from utils.fuzzy_matcher import find_journal_by_issn
                journal_row = find_journal_by_issn(journal_issn, df_local)
                
                if journal_row is not None:
                    article["revista_quartil"] = journal_row.get("Quartil JCR", "-")
                    article["revista_sjr"] = journal_row.get("SJR", "-")
                    article["revista_indexador"] = journal_row.get("Indexador", "-")
                else:
                    article["revista_quartil"] = "-"
                    article["revista_sjr"] = "-"
                    article["revista_indexador"] = "-"
            else:
                article["revista_quartil"] = "-"
                article["revista_sjr"] = "-"
                article["revista_indexador"] = "-"
            
            enriched.append(article)
        
        return enriched


def get_similar_articles_finder(email_openalex: Optional[str] = None) -> SimilarArticlesFinder:
    """
    Retorna instância do SimilarArticlesFinder
    
    Args:
        email_openalex: Email para OpenAlex
        
    Returns:
        Instância de SimilarArticlesFinder
    """
    return SimilarArticlesFinder(email_openalex)

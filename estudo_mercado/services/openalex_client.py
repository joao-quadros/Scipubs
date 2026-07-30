import requests
import logging

logger = logging.getLogger(__name__)

class OpenAlexMarketClient:
    """Cliente para busca de dados e tendências acadêmicas/científicas na OpenAlex API."""

    def __init__(self, email="contato@estudomercado.ai"):
        self.email = email
        self.base_url = "https://api.openalex.org"

    def search_market_topics(self, keywords: str, limit: int = 5) -> list:
        """Busca artigos recentes e tendências na OpenAlex sobre as palavras-chave do mercado."""
        if not keywords:
            return []
            
        url = f"{self.base_url}/works?search={requests.utils.quote(keywords)}&sort=cited_by_count:desc&per_page={limit}&mailto={self.email}"
        try:
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                results = r.json().get("results", [])
                topics = []
                for item in results:
                    title = item.get("title")
                    year = item.get("publication_year")
                    citations = item.get("cited_by_count", 0)
                    doi = item.get("doi")
                    topics.append({
                        "titulo": title,
                        "ano": year,
                        "citacoes": citations,
                        "doi": doi
                    })
                return topics
        except Exception as e:
            logger.warning(f"Erro ao buscar na OpenAlex: {e}")
        return []

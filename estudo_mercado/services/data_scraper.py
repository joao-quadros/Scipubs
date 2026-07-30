import requests
from bs4 import BeautifulSoup
import logging
from utils.formatting import truncate_text

logger = logging.getLogger(__name__)

def scrape_url_content(url: str, timeout: int = 5) -> str:
    """Raspa o conteúdo textual principal de uma URL de concorrente ou artigo."""
    if not url or not str(url).startswith("http"):
        return ""
        
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        r = requests.get(url, headers=headers, timeout=timeout, verify=False)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')

            # Remove scripts, styles e cabeçalhos desnecessários
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.extract()
                
            paragraphs = [p.text.strip() for p in soup.find_all('p') if len(p.text.strip()) > 30]
            full_text = " ".join(paragraphs)
            return truncate_text(full_text, max_len=1500)
    except Exception as e:
        logger.warning(f"Erro ao raspar URL {url}: {e}")
    return ""

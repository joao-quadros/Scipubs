# Funções auxiliares para busca de Objetivo e Escopo
# Usado por scripts/fetch_aims_scope.py e map_editorial_profile_v2.py

import requests
import re
from bs4 import BeautifulSoup
from typing import Optional
import logging

logger = logging.getLogger(__name__)

HEADERS = {"User-Agent": "SciPubs/1.0 (mailto:support@scipubs.com)"}
MAX_TEXT = 1500


def clean_text(text: str) -> str:
    """Limpa texto removendo HTML entities e normalizando."""
    if not text:
        return ""
    text = re.sub(r"&[a-z#]+;", " ", str(text))
    text = re.sub(r"\s+", " ", text).strip()
    return text[:MAX_TEXT] if len(text) > MAX_TEXT else text


def fetch_openalex(issn: str) -> Optional[str]:
    """Busca description + summary na OpenAlex."""
    if not issn or len(issn.replace("-", "").strip()) != 8:
        return None
    try:
        issn_clean = issn.replace("-", "").strip()
        url = f"https://api.openalex.org/sources/issn:{issn_clean}"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            desc = data.get("description", "") or ""
            summary = data.get("summary", "") or ""
            if desc and desc not in ["None", "none"]:
                return clean_text(f"{desc} {summary}")
    except Exception as e:
        logger.debug(f"OpenAlex error: {e}")
    return None


def fetch_scielo(issn: str) -> Optional[str]:
    """Busca mission na SciELO ArticleMeta API."""
    if not issn or len(issn.replace("-", "").strip()) != 8:
        return None
    try:
        issn_clean = issn.replace("-", "").strip()
        url = f"https://articlemeta.scielo.org/api/v1/journal/issn/{issn_clean}"
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            journal = data.get("journal", data)
            mission = None
            if isinstance(journal, dict):
                mission = journal.get("mission")
                if isinstance(mission, dict):
                    mission = mission.get("pt") or mission.get("en") or mission.get("es") or ""
                if mission and str(mission).strip() not in ["None", "none", ""]:
                    return clean_text(str(mission).strip())
    except Exception as e:
        logger.debug(f"SciELO error: {e}")
    return None


def fetch_crossref(issn: str) -> Optional[str]:
    """Busca description na CrossRef API."""
    if not issn or len(issn.replace("-", "").strip()) != 8:
        return None
    try:
        issn_clean = issn.replace("-", "").strip()
        url = f"https://api.crossref.org/journals/{issn_clean}"
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            message = data.get("message", {})
            description = message.get("description", "")
            if description and len(str(description).strip()) > 20:
                return clean_text(str(description).strip())
    except Exception as e:
        logger.debug(f"CrossRef error: {e}")
    return None


def fetch_from_homepage(url: str) -> Optional[str]:
    """Scraping da homepage ou páginas de Aims & Scope."""
    if not url or url in ["-", "", "nan", "None"] or not url.startswith("http"):
        return None
    
    patterns = [
        f"{url.rstrip('/')}/about",
        f"{url.rstrip('/')}/aims-and-scope",
        f"{url.rstrip('/')}/aims",
        f"{url.rstrip('/')}/scope",
    ]
    
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            content = []
            for p in soup.find_all(['p', 'div', 'span']):
                text = p.get_text(strip=True)
                if 100 <= len(text) <= 2000:
                    content.append(text)
            if content:
                return clean_text(' '.join(content[:10]))
    except:
        pass
    
    for pattern_url in patterns[:3]:
        try:
            resp = requests.get(pattern_url, headers=HEADERS, timeout=10)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                content = []
                for p in soup.find_all(['p', 'div', 'span']):
                    text = p.get_text(strip=True)
                    if 100 <= len(text) <= 2000:
                        content.append(text)
                if content:
                    return clean_text(' '.join(content[:15]))
        except:
            continue
    return None
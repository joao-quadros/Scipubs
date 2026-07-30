import requests
from bs4 import BeautifulSoup
import urllib.parse
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def search_google_snippet(journal_title):
    """Pesquisa no Google / DuckDuckGo por '[Título da Revista] Aims and scope' e extrai o snippet."""
    if not journal_title or str(journal_title).strip() in ["-", "", "nan", "None"]:
        return ""

    title_clean = str(journal_title).strip()
    query = f'"{title_clean}" Aims and scope'
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9,pt-BR;q=0.8,pt;q=0.7"
    }

    # 1. Tenta DuckDuckGo HTML
    try:
        url_ddg = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
        r = requests.get(url_ddg, headers=headers, timeout=5)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            snippets = soup.find_all('a', class_='result__snippet')
            for snip in snippets:
                text = re.sub(r'\s+', ' ', snip.text).strip()
                if len(text) > 30 and not any(ign in text.lower() for ign in ["captcha", "blocked", "javascript"]):
                    return text[:600]
    except Exception:
        pass

    # 2. Tenta Google Search HTML Direct
    try:
        url_google = f"https://www.google.com/search?q={urllib.parse.quote(query)}&hl=en"
        r = requests.get(url_google, headers=headers, timeout=5)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            # Procura divs de snippet do Google
            for div in soup.find_all(['div', 'span'], class_=re.compile(r'VwiC3b|yXK7lf|MUxGdf|Hg2fT', re.I)):
                text = re.sub(r'\s+', ' ', div.text).strip()
                if len(text) > 30:
                    return text[:600]
    except Exception:
        pass

    # 3. Tenta OpenAlex API como fallback rápido
    try:
        url_oa = f"https://api.openalex.org/sources?search={urllib.parse.quote(title_clean)}"
        r = requests.get(url_oa, timeout=4)
        if r.status_code == 200:
            results = r.json().get("results", [])
            if results:
                desc = results[0].get("description")
                if desc and len(desc) > 20:
                    return re.sub(r'\s+', ' ', desc).strip()[:600]
    except Exception:
        pass

    return ""

# Teste com alguns periódicos de exemplo
sample_journals = [
    "ACI MATERIALS JOURNAL",
    "ACTA PHYSICA POLONICA B",
    "ACTA PHYSIOLOGICA",
    "Musicae Scientiae"
]

print("--- TESTE DE PESQUISA DE SNIPPETS GOOGLE / DUCKDUCKGO ---")
for j in sample_journals:
    snip = search_google_snippet(j)
    print(f"\n🔹 Revista: {j}")
    print(f"   Query: \"{j}\" Aims and scope")
    print(f"   Snippet Extraído: {snip}")

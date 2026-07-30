import requests
import urllib.parse
import re
import sys
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def normalize_title(title):
    """Normaliza títulos em CAIXA ALTA, remove pontuações excessivas e parênteses."""
    if not title:
        return ""
    t = str(title).strip()
    # Converte caixa alta para Title Case inteligente
    if t.isupper():
        t = t.title()
    # Remove parênteses
    t = re.sub(r'\(.*?\)', '', t).strip()
    return t

def search_improved_snippet(journal_title, issn=None):
    """Estratégia melhorada: Busca sem aspas estritas + APIs acadêmicas de alta fidelidade."""
    t_clean = normalize_title(journal_title)
    if not t_clean:
        return ""

    # 1. Consulta OpenAlex Sources API por Título e ISSN
    try:
        url_oa = f"https://api.openalex.org/sources?search={urllib.parse.quote(t_clean)}"
        r = requests.get(url_oa, timeout=4)
        if r.status_code == 200:
            results = r.json().get("results", [])
            if results:
                desc = results[0].get("description")
                topics = [t.get("display_name") for t in results[0].get("topics", [])[:5] if t.get("display_name")]
                concepts = [c.get("display_name") for c in results[0].get("concepts", [])[:5] if c.get("display_name")]
                
                parts = []
                if desc and len(desc.strip()) > 25:
                    parts.append(re.sub(r'\s+', ' ', desc).strip())
                elif topics:
                    parts.append("Areas of Focus: " + ", ".join(topics))
                elif concepts:
                    parts.append("Key Concepts: " + ", ".join(concepts))
                    
                if parts:
                    return ". ".join(parts)[:600]
    except Exception:
        pass

    # 2. Busca DuckDuckGo sem aspas estritas
    query_flex = f"{t_clean} journal aims and scope description"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }
    try:
        url_ddg = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query_flex)}"
        r = requests.get(url_ddg, headers=headers, timeout=4)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            for snip in soup.find_all('a', class_='result__snippet'):
                txt = re.sub(r'\s+', ' ', snip.text).strip()
                if len(txt) > 35 and not any(ign in txt.lower() for ign in ["captcha", "blocked"]):
                    return txt[:600]
    except Exception:
        pass

    return ""

# Teste com amostragem de revistas que falharam
sample_failed = [
    "ACTA PHYSIOLOGICA",
    "ACTA POLYTECHNICA HUNGARICA",
    "ACTA PROTOZOOLOGICA",
    "ACTA RADIOLOGICA",
    "ACTA VETERINARIA BRASILICA",
    "ADVANCES IN ELECTRICAL AND COMPUTER ENGINEERING"
]

print("--- TESTE DA ESTRATÉGIA MELHORADA DE BUSCA ---")
for j in sample_failed:
    res = search_improved_snippet(j)
    print(f"\n🔹 Revista: {j}")
    print(f"   Título Normalizado: {normalize_title(j)}")
    print(f"   Resultado Extraído: {res[:250]}...")

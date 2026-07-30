"""
Script Avançado de Preenchimento Automático de Homepages de Periódicos
Este script combina a API do Crossref (identificação de editora oficial) e DuckDuckGo/Google 
para atribuir o link direto do site oficial da revista no arquivo dados.csv.
"""

import os
import sys
import time
import re
import urllib.request
import urllib.parse
import json
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(BASE_DIR, "dados.csv")

# Mapeamento de grandes editoras acadêmicas para suas URLs base de revistas
PUBLISHER_URL_MAP = {
    "taylor & francis": "https://www.tandfonline.com",
    "informa uk": "https://www.tandfonline.com",
    "elsevier": "https://www.sciencedirect.com",
    "springer": "https://link.springer.com",
    "nature": "https://www.nature.com",
    "ieee": "https://ieeexplore.ieee.org",
    "wiley": "https://onlinelibrary.wiley.com",
    "mdpi": "https://www.mdpi.com",
    "frontiers": "https://www.frontiersin.org",
    "oxford university press": "https://academic.oup.com",
    "cambridge university press": "https://www.cambridge.org/core",
    "sage": "https://journals.sagepub.com",
    "bmj": "https://www.bmj.com",
    "american chemical society": "https://pubs.acs.org",
    "american physical society": "https://journals.aps.org",
    "scielo": "https://www.scielo.org",
    "biomed central": "https://biomedcentral.com"
}

DOMINIOS_IGNORAR = [
    "duckduckgo.com", "google.com", "bing.com", "wikipedia.org", "facebook.com",
    "twitter.com", "x.com", "linkedin.com", "youtube.com", "amazon.com",
    "researchgate.net", "academia.edu", "reddit.com"
]

def buscar_crossref(issn):
    if not issn or issn in ["-", "nan", "None"]:
        return None
    
    clean_issn = str(issn).strip().replace(" ", "")
    url = f"https://api.crossref.org/journals/{clean_issn}"
    headers = {"User-Agent": "SciPubsBot/1.0 (mailto:admin@scipubs.com)"}
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as response:
            res = json.loads(response.read().decode("utf-8", errors="ignore"))
            msg = res.get("message", {})
            publisher = str(msg.get("publisher", "")).lower()
            
            for pub_key, pub_url in PUBLISHER_URL_MAP.items():
                if pub_key in publisher:
                    return pub_url
    except Exception:
        pass
    return None

def buscar_homepage_ddg(titulo_revista):
    query_str = f'"{titulo_revista}" official journal website'
    url_search = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote(query_str)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    
    try:
        req = urllib.request.Request(url_search, headers=headers)
        with urllib.request.urlopen(req, timeout=6) as response:
            html = response.read().decode("utf-8", errors="ignore")
            
        raw_links = re.findall(r'uddg=([^&"\']+)', html)
        for raw in raw_links:
            decoded = urllib.parse.unquote(raw)
            if not any(ign in decoded.lower() for ign in DOMINIOS_IGNORAR):
                if decoded.startswith("http://") or decoded.startswith("https://"):
                    return decoded
    except Exception:
        pass
    return None

def preencher_homepages(max_busca=300):
    print(f"Lendo base de dados: {CSV_PATH}...")
    df = pd.read_csv(CSV_PATH, low_memory=False)
    
    col_title = "Título da Revista" if "Título da Revista" in df.columns else df.columns[1]
    col_issn = "ISSN" if "ISSN" in df.columns else "ISSN"
    col_home = "Homepage"
    
    mask_missing = df[col_home].isna() | (df[col_home].astype(str).str.strip() == "-") | (df[col_home].astype(str).str.strip() == "")
    indices_faltantes = df[mask_missing].index.tolist()
    
    total_faltantes = len(indices_faltantes)
    print(f"Total de periódicos sem Homepage: {total_faltantes}")
    
    processados = 0
    encontrados = 0
    
    for idx in indices_faltantes:
        if processados >= max_busca:
            print(f"Limite máximo atingido ({max_busca}).")
            break
            
        row = df.loc[idx]
        titulo = str(row[col_title]).strip()
        issn = str(row.get(col_issn, "")).strip()
        
        if not titulo or titulo in ["-", "nan", "None"]:
            continue
            
        processados += 1
        print(f"[{processados}/{min(total_faltantes, max_busca)}] Resolvendo site para: '{titulo}' (ISSN: {issn})...")
        
        # 1. Tenta API do Crossref para identificar a editora oficial
        hp_encontrada = buscar_crossref(issn)
        
        # 2. Se não encontrou no Crossref, busca no DuckDuckGo
        if not hp_encontrada:
            hp_encontrada = buscar_homepage_ddg(titulo)
            
        if hp_encontrada:
            print(f"   --> Link encontrado: {hp_encontrada}")
            df.loc[idx, col_home] = hp_encontrada
            encontrados += 1
        else:
            print("   --> Nenhum link oficial encontrado.")
            
        if processados % 10 == 0:
            df.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")
            print("   [Progresso salvo no CSV]")
            
        time.sleep(0.3)
        
    df.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")
    print(f"\nFinalizado! Homepages atualizadas nesta sessão: {encontrados}/{processados}")

if __name__ == "__main__":
    limite = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    preencher_homepages(max_busca=limite)

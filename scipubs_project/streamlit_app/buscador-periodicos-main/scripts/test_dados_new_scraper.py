import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def clean_text(text):
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', str(text))
    return text.strip()

def fetch_openalex_details(issn, title):
    """Consulta OpenAlex para obter informações de escopo, tópicos e tipo de publicação."""
    if issn and str(issn).strip() not in ["-", "", "nan", "None"]:
        issn_clean = str(issn).replace("-", "").strip()
        url = f"https://api.openalex.org/sources/issn:{issn_clean}"
        try:
            r = requests.get(url, timeout=4, verify=False)
            if r.status_code == 200:
                data = r.json()
                desc = data.get("description")
                topics = [t.get("display_name") for t in data.get("topics", [])[:6] if t.get("display_name")]
                concepts = [c.get("display_name") for c in data.get("concepts", [])[:6] if c.get("display_name")]
                publisher = data.get("publisher", "")
                
                parts = []
                if desc and len(clean_text(desc)) > 20:
                    parts.append(clean_text(desc))
                elif topics:
                    parts.append("Tópicos Principais: " + ", ".join(topics))
                elif concepts:
                    parts.append("Conceitos Chave: " + ", ".join(concepts))
                    
                if parts:
                    return ". ".join(parts)
        except Exception:
            pass
    return ""

def fetch_doaj_details(issn, title):
    """Consulta DOAJ API para obter escopo, matérias e tipos de publicação."""
    if issn and str(issn).strip() not in ["-", "", "nan", "None"]:
        issn_clean = str(issn).replace("-", "").strip()
        if len(issn_clean) == 8:
            issn_fmt = f"{issn_clean[:4]}-{issn_clean[4:]}"
        else:
            issn_fmt = issn_clean
        url = f"https://doaj.org/api/v4/search/journals/issn:{issn_fmt}"
        try:
            r = requests.get(url, timeout=4, verify=False)
            if r.status_code == 200:
                data = r.json()
                results = data.get("results", [])
                if results:
                    bib = results[0].get("bibjson", {})
                    subjects = [s.get("term") for s in bib.get("subject", []) if s.get("term")]
                    keywords = bib.get("keywords", [])
                    parts = []
                    if subjects:
                        parts.append("Áreas de Conhecimento: " + ", ".join(subjects))
                    if keywords:
                        parts.append("Palavras-Chave: " + ", ".join(keywords))
                    if parts:
                        return ". ".join(parts)
        except Exception:
            pass
    return ""

def scrape_journal_profile(url):
    """Extrai Escopo, Missão e Tipos de Trabalhos Aceitos via Web Scraping da Homepage."""
    if not url or str(url).strip() in ["-", "", "nan", "None"]:
        return "", "", ""
        
    url_str = str(url).strip()
    if not url_str.startswith("http"):
        url_str = "http://" + url_str
        
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7,es;q=0.6"
    }
    
    try:
        r = requests.get(url_str, headers=headers, timeout=6, verify=False, allow_redirects=True)
        if r.status_code != 200:
            return "", "", ""
            
        soup = BeautifulSoup(r.text, 'html.parser')
        
        escopo_text = ""
        missao_text = ""
        tipos_text = ""

        # 1. Missão
        for el in soup.find_all(['div', 'section', 'p', 'span']):
            txt_raw = clean_text(el.text)
            txt_low = txt_raw.lower()
            if any(w in txt_low for w in ['nossa missão', 'missão:', 'mission statement', 'misión:']) and len(txt_raw) > 20:
                m_match = re.search(r'(?:nossa missão|missão|mission statement|misión)[:\s]*(.*)', txt_raw, re.I)
                if m_match and len(m_match.group(1).strip()) > 15:
                    missao_text = clean_text(m_match.group(1))[:300]
                    break
                elif len(txt_raw) < 400:
                    missao_text = txt_raw[:300]
                    break

        # 2. Tipos de Trabalhos Aceitos (ex: original articles, reviews, case reports, etc.)
        for el in soup.find_all(['div', 'section', 'p', 'li', 'ul']):
            txt_raw = clean_text(el.text)
            txt_low = txt_raw.lower()
            if any(w in txt_low for w in ['article types', 'types of papers', 'tipos de artigos', 'tipos de trabalhos', 'manuscript types', 'submissões aceitas']) and len(txt_raw) > 15:
                t_match = re.search(r'(?:article types|types of papers|tipos de artigos|tipos de trabalhos|manuscript types)[:\s]*(.*)', txt_raw, re.I)
                if t_match and len(t_match.group(1).strip()) > 10:
                    tipos_text = clean_text(t_match.group(1))[:250]
                    break
                elif len(txt_raw) < 300:
                    tipos_text = txt_raw[:250]
                    break

        # 3. Meta Description / Escopo
        meta = soup.find('meta', attrs={'name': re.compile(r'description', re.I)}) or soup.find('meta', property=re.compile(r'description', re.I))
        if meta and meta.get('content'):
            m_text = clean_text(meta.get('content'))
            if len(m_text) > 30 and not any(ign in m_text.lower() for ign in ["human", "captcha", "access denied", "robot"]):
                escopo_text = m_text[:600]

        # OJS Summary / About Block
        if not escopo_text:
            ojs_div = soup.find('div', class_=re.compile(r'journal-summary|homepage-about|about|description', re.I))
            if ojs_div:
                txt = clean_text(ojs_div.text)
                if len(txt) > 40:
                    escopo_text = txt[:600]

        # Parágrafos gerais no corpo do HTML
        if not escopo_text:
            candidates = []
            for p in soup.find_all('p'):
                txt = clean_text(p.text)
                txt_low = txt.lower()
                if len(txt) < 50:
                    continue
                if any(w in txt_low for w in ["publishes", "peer-reviewed", "scope", "aims to", "focuses on", "publica", "escopo", "editorial", "revista", "estudo"]):
                    candidates.append(txt)
            if candidates:
                escopo_text = "\n\n".join(candidates[:2])[:600]

        return escopo_text, missao_text, tipos_text

    except Exception:
        pass
    return "", "", ""

def process_journal(title, issn, homepage):
    escopo, missao, tipos = scrape_journal_profile(homepage)
    
    # Fallback para DOAJ e OpenAlex se necessário
    if not escopo or len(escopo) < 30:
        doaj_info = fetch_doaj_details(issn, title)
        if doaj_info:
            escopo = doaj_info
            
    if not escopo or len(escopo) < 20:
        oa_info = fetch_openalex_details(issn, title)
        if oa_info:
            escopo = oa_info

    if not escopo and not missao and not tipos:
        return "Informação não encontrada"

    parts = []
    if escopo:
        parts.append(f"Objetivo e Escopo: {escopo}")
    if missao:
        parts.append(f"Missão: {missao}")
    if tipos:
        parts.append(f"Tipos de Trabalhos Aceitos: {tipos}")
        
    return ". ".join(parts)

# Teste nos primeiros 10 registros de dados_new.csv
df = pd.read_csv('dados_new.csv', sep=',', encoding='latin-1', nrows=10)
col_title = df.columns[0]
col_issn = df.columns[1]
col_hp = df.columns[2]

print("--- TESTE DE PROCESSAMENTO (PRIMEIROS 10 PERIÓDICOS) ---")
for idx, row in df.iterrows():
    t_val = row[col_title]
    i_val = row[col_issn]
    h_val = row[col_hp]
    
    res = process_journal(t_val, i_val, h_val)
    print(f"\n[Revista {idx+1}] {t_val} (ISSN: {i_val})")
    print(f"URL: {h_val}")
    print(f"Perfil Editorial: {res[:300]}...")

import pandas as pd
import requests
from bs4 import BeautifulSoup
import os
import re
import time
import sys
import urllib.parse
import urllib3
from difflib import SequenceMatcher
from concurrent.futures import ThreadPoolExecutor, as_completed

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

MAX_WORKERS = 20
TIMEOUT = 4
BATCH_SIZE = 50

def clean_text(text):
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', str(text))
    return text.strip()

def normalizar(nome):
    import unicodedata
    nome = str(nome).lower().strip()
    nome = ''.join(c for c in unicodedata.normalize('NFD', nome) if unicodedata.category(c) != 'Mn')
    nome = re.sub(r'[^a-z0-9\s]', '', nome)
    return ' '.join(nome.split())

def fetch_openalex_aims(issn, title):
    if issn and str(issn).strip() not in ["-", "", "nan", "None"]:
        issn_clean = str(issn).replace("-", "").strip()
        url = f"https://api.openalex.org/sources/issn:{issn_clean}"
        try:
            r = requests.get(url, timeout=3, verify=False)
            if r.status_code == 200:
                data = r.json()
                desc = data.get("description")
                if desc and len(clean_text(desc)) > 30:
                    return clean_text(desc)
                    
                topics = [t.get("display_name") for t in data.get("topics", [])[:6] if t.get("display_name")]
                concepts = [c.get("display_name") for c in data.get("concepts", [])[:6] if c.get("display_name")]
                publisher = data.get("publisher", "")
                
                parts = []
                if publisher:
                    parts.append(f"Publisher: {publisher}")
                if topics:
                    parts.append("Scope Topics: " + ", ".join(topics))
                elif concepts:
                    parts.append("Key Concepts: " + ", ".join(concepts))
                if parts:
                    return ". ".join(parts)
        except Exception:
            pass
    return ""

def fetch_doaj_aims(issn, title):
    if issn and str(issn).strip() not in ["-", "", "nan", "None"]:
        issn_clean = str(issn).replace("-", "").strip()
        if len(issn_clean) == 8:
            issn_fmt = f"{issn_clean[:4]}-{issn_clean[4:]}"
        else:
            issn_fmt = issn_clean
        url = f"https://doaj.org/api/v4/search/journals/issn:{issn_fmt}"
        try:
            r = requests.get(url, timeout=3, verify=False)
            if r.status_code == 200:
                data = r.json()
                results = data.get("results", [])
                if results:
                    bib = results[0].get("bibjson", {})
                    subjects = [s.get("term") for s in bib.get("subject", []) if s.get("term")]
                    keywords = bib.get("keywords", [])
                    parts = []
                    if subjects:
                        parts.append("Subjects: " + ", ".join(subjects))
                    if keywords:
                        parts.append("Keywords: " + ", ".join(keywords))
                    if parts:
                        return ". ".join(parts)
        except Exception:
            pass
    return ""

def scrape_homepage_aims(url):
    if not url or str(url).strip() in ["-", "", "nan", "None"]:
        return ""
        
    url_str = str(url).strip()
    if not url_str.startswith("http"):
        url_str = "http://" + url_str
        
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,pt-BR;q=0.8,es;q=0.7"
    }
    
    try:
        r = requests.get(url_str, headers=headers, timeout=TIMEOUT, verify=False, allow_redirects=True)
        if r.status_code != 200:
            return ""
            
        soup = BeautifulSoup(r.text, 'html.parser')
        
        mission_text = ""
        aims_text = ""

        # 0. Busca por Bloco de Missão / Mission
        for el in soup.find_all(['div', 'section', 'p', 'span']):
            txt_raw = clean_text(el.text)
            txt_low = txt_raw.lower()
            if any(w in txt_low for w in ['nossa missão', 'missão:', 'mission statement', 'misión:']) and len(txt_raw) > 25:
                m_match = re.search(r'(?:nossa missão|missão|mission statement|misión)[:\s]*(.*)', txt_raw, re.I)
                if m_match and len(m_match.group(1).strip()) > 15:
                    mission_text = "Missão: " + clean_text(m_match.group(1))[:400]
                    break
                elif len(txt_raw) < 450:
                    mission_text = "Missão: " + txt_raw
                    break

        # 1. Meta Description
        meta = soup.find('meta', attrs={'name': re.compile(r'description', re.I)}) or soup.find('meta', property=re.compile(r'description', re.I))
        if meta and meta.get('content'):
            m_text = clean_text(meta.get('content'))
            if len(m_text) > 30 and not any(ign in m_text.lower() for ign in ["human", "captcha", "access denied", "robot"]):
                aims_text = m_text[:800]

        # 2. OJS Summary / About Block
        if not aims_text:
            ojs_div = soup.find('div', class_=re.compile(r'journal-summary|homepage-about|about|description', re.I))
            if ojs_div:
                txt = clean_text(ojs_div.text)
                if len(txt) > 40:
                    aims_text = txt[:800]

        # 3. Divs/Seções com ID ou classe contendo aims, scope, about, overview
        if not aims_text:
            target_sec = soup.find(re.compile(r'div|section|article'), id=re.compile(r'aims|scope|about|overview|intro', re.I)) or \
                         soup.find(re.compile(r'div|section|article'), class_=re.compile(r'aims|scope|about|overview|intro|journal-summary', re.I))
            if target_sec:
                sec_text = clean_text(target_sec.text)
                if len(sec_text) > 40:
                    aims_text = sec_text[:800]

        # 4. Parágrafos gerais no corpo do HTML
        if not aims_text:
            candidates = []
            for p in soup.find_all('p'):
                txt = clean_text(p.text)
                txt_low = txt.lower()
                if len(txt) < 50:
                    continue
                if any(w in txt_low for w in ["publishes", "peer-reviewed", "scope", "aims to", "focuses on", "publica", "escopo", "editorial", "revista", "estudo"]):
                    candidates.append(txt)
            if candidates:
                aims_text = "\n\n".join(candidates[:2])[:800]

        if mission_text and aims_text:
            if mission_text.lower() in aims_text.lower():
                return aims_text
            return f"{mission_text}. {aims_text}"
        elif mission_text:
            return mission_text
        elif aims_text:
            return aims_text

    except Exception:
        pass
    return ""

def fetch_h5_metrics(journal_title):
    if not journal_title or str(journal_title).strip() in ["-", "", "nan", "None"]:
        return "", ""

    title_norm = normalizar(journal_title)
    url_gs = f"https://scholar.google.com/citations?hl=pt-BR&view_op=search_venues&vq={urllib.parse.quote(journal_title)}&btnG="
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7"
    }

    try:
        r = requests.get(url_gs, headers=headers, timeout=3, verify=False)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            table = soup.find('table', id='gsc_mp_table') or soup.find('table')
            if table:
                rows = table.find_all('tr')
                for tr in rows[1:]:
                    tds = [td.text.strip() for td in tr.find_all(['td', 'th'])]
                    if len(tds) >= 4:
                        pub_name = tds[1]
                        h5_idx = tds[2]
                        h5_med = tds[3]
                        
                        score = SequenceMatcher(None, title_norm, normalizar(pub_name)).ratio()
                        if score >= 0.75:
                            return h5_idx, h5_med
    except Exception:
        pass
    return "", ""

def process_row(idx, title, issn, homepage):
    res_scope = scrape_homepage_aims(homepage)
    if not res_scope or len(res_scope) < 30:
        res_scope = fetch_doaj_aims(issn, title)
    if not res_scope or len(res_scope) < 20:
        res_scope = fetch_openalex_aims(issn, title)

    h5_idx, h5_med = fetch_h5_metrics(title)
    return idx, res_scope, h5_idx, h5_med

def run_enrichment(file_path="dados_2.csv", limit=None):
    if not os.path.exists(file_path):
        print(f"Arquivo {file_path} não encontrado.")
        return

    print(f"--- Iniciando Enriquecimento Único (Aims & Scope + Missão + Índice h5 + Mediana h5) em {file_path} ---")
    
    df = pd.read_csv(file_path, sep=';', encoding='utf-8-sig', low_memory=False)

    col_title = df.columns[0]
    col_aims = "Aims and Scope"
    col_h5_idx = "Índice h5"
    col_h5_med = "Mediana h5"

    if col_aims not in df.columns:
        df[col_aims] = ""

    if col_h5_idx not in df.columns:
        df[col_h5_idx] = ""

    if col_h5_med not in df.columns:
        idx_h5 = df.columns.get_loc(col_h5_idx) if col_h5_idx in df.columns else len(df.columns) - 1
        df.insert(idx_h5 + 1, col_h5_med, "")

    df[col_aims] = df[col_aims].astype(object).fillna("").astype(str)
    df[col_h5_idx] = df[col_h5_idx].astype(object).fillna("").astype(str)
    df[col_h5_med] = df[col_h5_med].astype(object).fillna("").astype(str)

    mask_empty = (df[col_aims].isna() | (df[col_aims].astype(str).str.strip() == "") | (df[col_aims].astype(str).str.strip() == "-")) | \
                 (df[col_h5_med].isna() | (df[col_h5_med].astype(str).str.strip() == "") | (df[col_h5_med].astype(str).str.strip() == "-"))
    
    indices = df[mask_empty].index.tolist()
    
    if limit:
        indices = indices[:limit]
        
    total = len(indices)
    print(f"Total de revistas a processar nesta rodada: {total}")

    if total == 0:
        print("Todas as revistas já possuem dados de Escopo e Métricas h5!")
        return

    success_count = 0
    start_time = time.time()

    for i in range(0, total, BATCH_SIZE):
        batch_indices = indices[i:i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        total_batches = (total + BATCH_SIZE - 1) // BATCH_SIZE
        print(f"\n[Lote {batch_num}/{total_batches}] Processando revistas {i+1} a {i+len(batch_indices)} de {total}...")
        
        batch_results = []
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {
                executor.submit(process_row, idx, str(df.loc[idx, col_title]), str(df.loc[idx].get("ISSN", "")), str(df.loc[idx].get("Homepage", ""))): idx
                for idx in batch_indices
            }

            for future in as_completed(futures):
                idx = futures[future]
                try:
                    res_idx, res_scope, h5_idx, h5_med = future.result()
                    batch_results.append((res_idx, res_scope, h5_idx, h5_med))
                except Exception:
                    pass

        # Recarrega o CSV mais recente do disco antes de aplicar o lote para garantir total integridade
        df_latest = pd.read_csv(file_path, sep=';', encoding='utf-8-sig', low_memory=False)
        if col_h5_med not in df_latest.columns:
            idx_h5 = df_latest.columns.get_loc(col_h5_idx) if col_h5_idx in df_latest.columns else len(df_latest.columns) - 1
            df_latest.insert(idx_h5 + 1, col_h5_med, "")

        df_latest[col_aims] = df_latest[col_aims].astype(object).fillna("").astype(str)
        df_latest[col_h5_idx] = df_latest[col_h5_idx].astype(object).fillna("").astype(str)
        df_latest[col_h5_med] = df_latest[col_h5_med].astype(object).fillna("").astype(str)

        batch_success = 0
        for res_idx, res_scope, h5_idx, h5_med in batch_results:
            updated = False
            if res_scope:
                df_latest.at[res_idx, col_aims] = str(res_scope)
                updated = True
            if h5_idx:
                df_latest.at[res_idx, col_h5_idx] = str(h5_idx)
                updated = True
            if h5_med:
                df_latest.at[res_idx, col_h5_med] = str(h5_med)
                updated = True
            if updated:
                batch_success += 1
                success_count += 1

        # Salva o arquivo CSV atualizado
        df_latest.to_csv(file_path, sep=';', index=False, encoding='utf-8-sig')
        elapsed = time.time() - start_time
        print(f"[OK] Lote {batch_num} salvo! +{batch_success} atualizadas neste lote (Total: {success_count} | {elapsed/60:.1f} min decorridos).")

    print(f"\n[FIM] Processamento concluído! Total de {success_count} revistas enriquecidas em {file_path}.")

if __name__ == "__main__":
    limit_val = int(sys.argv[1]) if len(sys.argv) > 1 else None
    run_enrichment("dados_2.csv", limit=limit_val)

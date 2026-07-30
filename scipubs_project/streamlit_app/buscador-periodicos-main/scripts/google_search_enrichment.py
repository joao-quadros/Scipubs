import pandas as pd
import requests
from bs4 import BeautifulSoup
import urllib.parse
import re
import os
import sys
import time
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuração de sys.stdout para UTF-8 no Windows
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

MAX_WORKERS = 20  # 20 trabalhadores simultâneos
BATCH_SIZE = 100

def clean_text(text):
    if not text:
        return ""
    # Remove quebras de linha, tabulações e caracteres que quebram CSV
    text = re.sub(r'[\r\n\t]+', ' ', str(text))
    text = re.sub(r'\s+', ' ', text)
    text = text.replace('"', "'").replace(";", ",")
    return text.strip()

def normalize_journal_title(title):
    """Normaliza títulos em CAIXA ALTA, remove parênteses e caracteres irrelevantes."""
    if not title or str(title).strip() in ["-", "", "nan", "None"]:
        return ""
    t = str(title).strip()
    if t.isupper():
        t = t.title()
    t = re.sub(r'\(.*?\)', '', t).strip()
    t = re.sub(r'[^a-zA-Z0-9\s\&\-\:]', '', t).strip()
    return t

def translate_to_academic_english(text):
    """Traduz textos para Inglês Acadêmico via Google GTX API."""
    if not text or str(text).strip() in ["-", "", "nan", "None", "Informação não encontrada"]:
        return ""

    text_clean = clean_text(text)
    if len(text_clean) < 10:
        return text_clean

    text_low = text_clean.lower()
    english_keywords = ["the ", " journal", "publishes ", "peer-reviewed", "research", "aims to", "focuses on", "scope of"]
    if sum(1 for w in english_keywords if w in text_low) >= 2:
        return text_clean

    try:
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=en&dt=t&q={urllib.parse.quote(text_clean[:2000])}"
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            res_json = r.json()
            sentences = res_json[0]
            translated_text = "".join([s[0] for s in sentences if s and len(s) > 0 and s[0]])
            if translated_text and len(translated_text.strip()) > 5:
                return clean_text(translated_text)
    except Exception:
        pass
    return text_clean

def fetch_multi_source_journal_scope(journal_title, issn=None):
    """Busca em Múltiplas Fontes (OpenAlex + Crossref + DOAJ + DuckDuckGo + Bing) sem inserir texto de fallback."""
    t_clean = normalize_journal_title(journal_title)
    if not t_clean:
        return ""

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9,pt-BR;q=0.8"
    }

    # 1. OpenAlex API (JSON estruturado de alta precisão)
    try:
        query_oa = f"https://api.openalex.org/sources?search={urllib.parse.quote(t_clean)}"
        r = requests.get(query_oa, timeout=4)
        if r.status_code == 200:
            results = r.json().get("results", [])
            if results:
                desc = results[0].get("description")
                topics = [t.get("display_name") for t in results[0].get("topics", [])[:6] if t.get("display_name")]
                concepts = [c.get("display_name") for c in results[0].get("concepts", [])[:6] if c.get("display_name")]
                
                parts = []
                if desc and len(desc.strip()) > 25:
                    parts.append(clean_text(desc))
                elif topics:
                    parts.append("Aims and Scope: Focuses on " + ", ".join(topics))
                elif concepts:
                    parts.append("Aims and Scope: Research areas in " + ", ".join(concepts))
                    
                if parts:
                    return ". ".join(parts)[:600]
    except Exception:
        pass

    # 2. DOAJ API por ISSN
    if issn and str(issn).strip() not in ["-", "", "nan", "None"]:
        try:
            issn_clean = str(issn).replace("-", "").strip()
            url_doaj = f"https://doaj.org/api/v4/search/journals/issn:{issn_clean}"
            r = requests.get(url_doaj, timeout=4)
            if r.status_code == 200:
                results = r.json().get("results", [])
                if results:
                    bib = results[0].get("bibjson", {})
                    subjects = [s.get("term") for s in bib.get("subject", []) if s.get("term")]
                    keywords = bib.get("keywords", [])
                    if subjects or keywords:
                        return f"Aims and Scope: Subject areas include {', '.join(subjects)}. Keywords: {', '.join(keywords)}."
        except Exception:
            pass

    # 3. DuckDuckGo Search Snippet
    try:
        query_flex = f"{t_clean} journal aims and scope description"
        url_ddg = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query_flex)}"
        r = requests.get(url_ddg, headers=headers, timeout=4)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            snippets = soup.find_all('a', class_='result__snippet')
            for snip in snippets:
                txt = clean_text(snip.text)
                if len(txt) > 35 and not any(ign in txt.lower() for ign in ["captcha", "blocked", "enable javascript"]):
                    return txt[:600]
    except Exception:
        pass

    # 4. Bing Search Snippet
    try:
        query_bing = f"{t_clean} editorial scope aims"
        url_bing = f"https://www.bing.com/search?q={urllib.parse.quote(query_bing)}&setlang=en"
        r = requests.get(url_bing, headers=headers, timeout=4)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            for p in soup.find_all('p', class_=re.compile(r'b_algo|b_caption', re.I)):
                txt = clean_text(p.text)
                if len(txt) > 35:
                    return txt[:600]
    except Exception:
        pass

    # SE NÃO ENCONTRAR, RETORNA VAZIO "" (NÃO INSERE 'Informação não encontrada')
    return ""

def process_row_search(idx, row):
    col_title = row.index[0]
    col_issn = row.index[1]

    title = str(row.get(col_title, ""))
    issn = str(row.get(col_issn, ""))

    snippet_text = fetch_multi_source_journal_scope(title, issn)

    if not snippet_text or len(snippet_text) < 15:
        scope_pt = ""
        scope_en = ""
    else:
        scope_pt = clean_text(snippet_text)
        scope_en = translate_to_academic_english(snippet_text)

    return idx, scope_pt, scope_en

def run_google_snippet_search(file_path="dados_Antigravity.csv", limit=None):
    if not os.path.exists(file_path):
        print(f"Arquivo {file_path} não encontrado.")
        return

    print(f"--- Executando Mineração Multi-Fonte (Memory-Safe + CSV Quoting) em {file_path} ---")
    df = pd.read_csv(file_path, sep=';', encoding='utf-8-sig', on_bad_lines='skip', low_memory=False)

    col_scope = "Aims and Scope"
    col_trans = "Aims and Scope (translate)"

    if col_scope not in df.columns:
        df.insert(3, col_scope, "")
    if col_trans not in df.columns:
        df.insert(4, col_trans, "")

    df[col_scope] = df[col_scope].astype("object").fillna("").astype(str)
    df[col_trans] = df[col_trans].astype("object").fillna("").astype(str)

    # Limpeza robusta via Regex
    mask_c1 = df[col_scope].str.contains("não encontrada|not found|nao encontrada", case=False, na=False)
    df.loc[mask_c1, col_scope] = ""
    mask_c2 = df[col_trans].str.contains("not found|não encontrada|nao encontrada", case=False, na=False)
    df.loc[mask_c2, col_trans] = ""

    # Seleciona linhas verdadeiramente vazias
    mask_pending = df[col_scope].isna() | (df[col_scope].astype(str).str.strip() == "") | (df[col_scope].astype(str).str.strip() == "-")
    pending_indices = df[mask_pending].index.tolist()

    if limit:
        pending_indices = pending_indices[:limit]

    total = len(pending_indices)
    print(f"Total de periódicos vazios pendentes para busca: {total}")

    if total == 0:
        print("Todos os periódicos já possuem escopo cadastrado!")
        return

    success_count = 0
    start_time = time.time()

    for i in range(0, total, BATCH_SIZE):
        batch_indices = pending_indices[i:i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        total_batches = (total + BATCH_SIZE - 1) // BATCH_SIZE
        print(f"\n[Lote {batch_num}/{total_batches}] Pesquisando revistas {i+1} a {i+len(batch_indices)} de {total}...")

        batch_results = []
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {
                executor.submit(process_row_search, idx, df.iloc[idx]): idx
                for idx in batch_indices
            }

            for future in as_completed(futures):
                idx = futures[future]
                try:
                    res_idx, pt_text, en_text = future.result()
                    batch_results.append((res_idx, pt_text, en_text))
                except Exception:
                    pass

        batch_new_success = 0
        for res_idx, pt_text, en_text in batch_results:
            df.loc[res_idx, col_scope] = clean_text(pt_text)
            df.loc[res_idx, col_trans] = clean_text(en_text)
            if pt_text and pt_text != "":
                batch_new_success += 1
                success_count += 1

        # Limpeza robusta antes da gravação
        mask_s1 = df[col_scope].astype(str).str.contains("não encontrada|not found", case=False, na=False)
        df.loc[mask_s1, col_scope] = ""
        mask_s2 = df[col_trans].astype(str).str.contains("not found|não encontrada", case=False, na=False)
        df.loc[mask_s2, col_trans] = ""

        # Salva o DataFrame mantido em memória sem reler do disco
        df.to_csv(file_path, sep=';', index=False, encoding='utf-8-sig', quoting=csv.QUOTE_ALL)

        elapsed = time.time() - start_time
        rate = (i + len(batch_indices)) / max(1, elapsed)
        rem_sec = (total - (i + len(batch_indices))) / max(0.1, rate)
        print(f"[OK] Lote {batch_num} salvo! +{len(batch_results)} processadas (+{batch_new_success} novos escopos | Total extraído nesta fase: {success_count} | {elapsed/60:.1f} min decorridos | Est. restante: {rem_sec/60:.1f} min).")

    print(f"\n[FIM] Mineração concluída com sucesso em {file_path}!")

if __name__ == "__main__":
    limit_val = int(sys.argv[1]) if len(sys.argv) > 1 else None
    run_google_snippet_search("dados_Antigravity.csv", limit=limit_val)

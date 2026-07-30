import pandas as pd
import requests
from bs4 import BeautifulSoup
import urllib.parse
import re
import os
import sys
import time
import csv
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuração de sys.stdout para UTF-8 no Windows
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

MAX_WORKERS = 20  # Reduzido levemente para evitar gargalo de banda e timeouts
BATCH_SIZE = 100
TARGET_FILE = "dados_Antigravity_novo.csv"
PROGRESS_FILE = "scripts/mining_progress.json"

# Headers globais simulando um navegador real
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9"
}

# User-Agent específico e polido para chamadas de APIs científicas e Wikipedia
WIKI_HEADERS = {
    "User-Agent": "JournalMetadataMiner/1.0 (mailto:jquad@gmail.com)"
}

def clean_text(text):
    if not text:
        return ""
    text = re.sub(r'[\r\n\t]+', ' ', str(text))
    text = re.sub(r'\s+', ' ', text)
    text = text.replace('"', "'").replace(";", ",")
    # Remove marcações HTML que podem vir de snippets do Wikipedia (ex: <span class="searchmatch">)
    text = re.sub(r'<[^>]+>', '', text)
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

def fetch_journal_scope_multi_source(session, title, issn=None, homepage=None):
    """Mineração de Alta Eficácia Otimizada com Wikipedia + Crossref + DOAJ + Bing."""
    t_clean = normalize_journal_title(title)
    if not t_clean:
        return ""

    # 1. Wikipedia API (Super rápido, confiável e sem rate limits)
    try:
        url_wiki = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(t_clean)}&format=json&utf8="
        r = session.get(url_wiki, headers=WIKI_HEADERS, timeout=4)
        if r.status_code == 200:
            results = r.json().get("query", {}).get("search", [])
            for res in results[:2]:
                snippet = res.get("snippet", "")
                title_wiki = res.get("title", "")
                # Se o título bater parcialmente ou contiver termos do periódico, extrai o snippet
                if len(snippet) > 35 and any(term in title_wiki.lower() for term in t_clean.lower().split()[:2]):
                    return f"Aims and Scope: {clean_text(snippet)}"
    except Exception:
        pass

    # 2. Crossref API por ISSN ou por Título
    if issn and str(issn).strip() not in ["-", "", "nan", "None"]:
        try:
            issn_clean = str(issn).strip()
            url_cr = f"https://api.crossref.org/journals/{issn_clean}"
            r = session.get(url_cr, headers=WIKI_HEADERS, timeout=4)
            if r.status_code == 200:
                msg = r.json().get("message", {})
                publisher = msg.get("publisher", "")
                title_cr = msg.get("title", "")
                if publisher:
                    return f"Aims and Scope: Published by {publisher}. Focuses on scholarly research in the field of {title_cr}."
        except Exception:
            pass

    try:
        url_cr_q = f"https://api.crossref.org/journals?query={urllib.parse.quote(t_clean)}"
        r = session.get(url_cr_q, headers=WIKI_HEADERS, timeout=4)
        if r.status_code == 200:
            items = r.json().get("message", {}).get("items", [])
            if items:
                publisher = items[0].get("publisher", "")
                title_cr = items[0].get("title", "")
                if publisher:
                    return f"Aims and Scope: Published by {publisher}. Focuses on academic publications in {title_cr}."
    except Exception:
        pass

    # 3. DOAJ API por ISSN
    if issn and str(issn).strip() not in ["-", "", "nan", "None"]:
        try:
            issn_clean = str(issn).replace("-", "").strip()
            url_doaj = f"https://doaj.org/api/v4/search/journals/issn:{issn_clean}"
            r = session.get(url_doaj, timeout=4)
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

    # 4. Raspagem Direta da Homepage
    if homepage and str(homepage).strip().startswith("http"):
        try:
            hp_url = str(homepage).strip()
            r_hp = session.get(hp_url, headers=HEADERS, timeout=4, verify=False)
            if r_hp.status_code == 200:
                soup_hp = BeautifulSoup(r_hp.text, 'html.parser')
                meta_desc = soup_hp.find('meta', attrs={'name': re.compile(r'description|abstract', re.I)})
                if meta_desc and meta_desc.get('content'):
                    txt_meta = clean_text(meta_desc['content'])
                    if len(txt_meta) > 30 and not any(ign in txt_meta.lower() for ign in ["cookie", "javascript"]):
                        return txt_meta[:600]
        except Exception:
            pass

    # 5. OpenAlex API (Fallback rápido caso a cota global deles não esteja excedida no momento)
    try:
        query_oa = f"https://api.openalex.org/sources?search={urllib.parse.quote(t_clean)}"
        r = session.get(query_oa, timeout=4)
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

    # 6. Bing Search Snippet (Fallback)
    try:
        query_bing = f"{t_clean} editorial scope aims"
        url_bing = f"https://www.bing.com/search?q={urllib.parse.quote(query_bing)}&setlang=en"
        r = session.get(url_bing, headers=HEADERS, timeout=4)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            for p in soup.find_all('p', class_=re.compile(r'b_algo|b_caption', re.I)):
                txt = clean_text(p.text)
                if len(txt) > 35:
                    return txt[:600]
    except Exception:
        pass

    return ""

def process_row(session, idx, row):
    col_title = row.index[0]
    col_issn = row.index[1]
    col_hp = row.index[2] if len(row.index) > 2 else None

    title = str(row.get(col_title, ""))
    issn = str(row.get(col_issn, ""))
    hp = str(row.get(col_hp, "")) if col_hp else ""

    snippet_text = fetch_journal_scope_multi_source(session, title, issn, hp)

    if not snippet_text or len(snippet_text) < 15:
        scope_pt = ""
        scope_en = ""
    else:
        scope_pt = clean_text(snippet_text)
        scope_en = translate_to_academic_english(snippet_text)

    return idx, scope_pt, scope_en

def run_high_efficacy_mining():
    if not os.path.exists(TARGET_FILE):
        print(f"Erro: Arquivo {TARGET_FILE} não foi encontrado.")
        return

    print(f"--- Iniciando Mineração de Alta Eficácia Otimizada em {TARGET_FILE} ---")
    df = pd.read_csv(TARGET_FILE, sep=';', encoding='utf-8-sig', on_bad_lines='skip', low_memory=False)

    col_scope = "Aims and Scope"
    col_trans = "Aims and Scope (translate)"

    if col_scope not in df.columns:
        df.insert(3, col_scope, "")
    if col_trans not in df.columns:
        df.insert(4, col_trans, "")

    df[col_scope] = df[col_scope].astype("object").fillna("").astype(str)
    df[col_trans] = df[col_trans].astype("object").fillna("").astype(str)

    # Limpa expressões fallback antigas
    mask_c1 = df[col_scope].str.contains("não encontrada|not found|nao encontrada", case=False, na=False)
    df.loc[mask_c1, col_scope] = ""
    mask_c2 = df[col_trans].str.contains("not found|não encontrada|nao encontrada", case=False, na=False)
    df.loc[mask_c2, col_trans] = ""

    # Identifica linhas pendentes vazias
    mask_pending = df[col_scope].isna() | (df[col_scope].astype(str).str.strip() == "") | (df[col_scope].astype(str).str.strip() == "-")
    pending_indices = df[mask_pending].index.tolist()

    total = len(pending_indices)
    print(f"Total de revistas a minerar em {TARGET_FILE}: {total}")

    if total == 0:
        print("Todas as revistas já possuem escopo cadastrado!")
        with open(PROGRESS_FILE, 'w') as f:
            json.dump({"total": len(df), "processed": len(df), "pending": 0, "success": 0}, f)
        return

    success_count = 0
    start_time = time.time()

    # Reutiliza sessões HTTP persistentes por thread worker
    sessions = [requests.Session() for _ in range(MAX_WORKERS)]

    for i in range(0, total, BATCH_SIZE):
        batch_indices = pending_indices[i:i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        total_batches = (total + BATCH_SIZE - 1) // BATCH_SIZE

        batch_results = []
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {}
            for j, idx in enumerate(batch_indices):
                session = sessions[j % MAX_WORKERS]
                futures[executor.submit(process_row, session, idx, df.iloc[idx])] = idx

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

        # Limpeza robusta
        mask_s1 = df[col_scope].astype(str).str.contains("não encontrada|not found", case=False, na=False)
        df.loc[mask_s1, col_scope] = ""
        mask_s2 = df[col_trans].astype(str).str.contains("not found|não encontrada", case=False, na=False)
        df.loc[mask_s2, col_trans] = ""

        # Salva mantendo DataFrame em memória
        df.to_csv(TARGET_FILE, sep=';', index=False, encoding='utf-8-sig', quoting=csv.QUOTE_ALL)

        processed_so_far = i + len(batch_indices)
        pending_remaining = total - processed_so_far

        # Grava progresso no arquivo JSON
        progress_data = {
            "total": total,
            "processed": processed_so_far,
            "pending": pending_remaining,
            "success": success_count
        }
        with open(PROGRESS_FILE, 'w') as f:
            json.dump(progress_data, f)

        elapsed = time.time() - start_time
        rate = processed_so_far / max(1, elapsed)
        rem_sec = pending_remaining / max(0.1, rate)
        print(f"[OK] Lote {batch_num}/{total_batches} salvo! {processed_so_far} processadas (+{batch_new_success} escopos | {elapsed/60:.1f} min decorridos).")

    print(f"\n[FIM] Mineração concluída com sucesso em {TARGET_FILE}!")

if __name__ == "__main__":
    run_high_efficacy_mining()

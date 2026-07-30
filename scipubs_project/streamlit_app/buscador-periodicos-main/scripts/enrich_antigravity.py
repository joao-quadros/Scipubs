import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import urllib3
import os
import sys
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuração de sys.stdout para UTF-8 no Windows
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

MAX_WORKERS = 25
BATCH_SIZE = 100

def clean_text(text):
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', str(text))
    return text.strip()

def build_known_catalog_map():
    """Cria um mapa unificado de revistas já mineradas para reutilização instantânea."""
    known_map = {}
    catalog_files = ['dados_complemento.csv', 'dados_2.csv', 'dados_new_atualizado.csv', 'dados_parcial.csv']
    for filename in catalog_files:
        if os.path.exists(filename):
            try:
                # Tenta sep ';' e depois ','
                try:
                    df_cat = pd.read_csv(filename, sep=';', encoding='utf-8-sig', low_memory=False)
                except Exception:
                    df_cat = pd.read_csv(filename, sep=',', encoding='latin-1', low_memory=False)

                col_title = df_cat.columns[0]
                col_scope = "Aims and Scope" if "Aims and Scope" in df_cat.columns else None
                col_issn = "ISSN" if "ISSN" in df_cat.columns else None

                if col_scope:
                    for _, row in df_cat.iterrows():
                        scope_val = clean_text(str(row.get(col_scope, "")))
                        if scope_val and scope_val not in ["-", "", "nan", "None", "Informação não encontrada"]:
                            t_norm = clean_text(str(row.get(col_title, ""))).lower()
                            if t_norm and t_norm not in known_map:
                                known_map[t_norm] = scope_val

                            if col_issn:
                                issn_val = clean_text(str(row.get(col_issn, ""))).replace("-", "").lower()
                                if issn_val and issn_val not in known_map:
                                    known_map[issn_val] = scope_val
            except Exception as e:
                pass
    print(f"[CATÁLOGO UNIFICADO] {len(known_map)} perfis de periódicos mapeados para reutilização.")
    return known_map

def translate_to_academic_english(text):
    """Traduz textos em português/espanhol/outros idiomas para Inglês Acadêmico via Google GTX API."""
    if not text or str(text).strip() in ["-", "", "nan", "None", "Informação não encontrada"]:
        return "Information not found" if str(text).strip() == "Informação não encontrada" else ""

    text_clean = clean_text(text)
    if len(text_clean) < 10:
        return text_clean

    text_low = text_clean.lower()
    english_keywords = ["the ", " journal", "publishes ", "peer-reviewed", "research", "aims to", "focuses on", "scope of"]
    if sum(1 for w in english_keywords if w in text_low) >= 3:
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

def fetch_sage_description(url, title):
    """Extrai a seção Overview/Description para revistas SAGE Publications."""
    if url and "sagepub.com" in str(url).lower():
        try:
            r = requests.get(url, timeout=5, verify=False)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, 'html.parser')
                desc_div = soup.find('div', class_=re.compile(r'overview|journal-description|journal-about', re.I))
                if desc_div:
                    return clean_text(desc_div.text)[:600]
                meta = soup.find('meta', attrs={'name': re.compile(r'description', re.I)})
                if meta and meta.get('content'):
                    return clean_text(meta.get('content'))[:600]
        except Exception:
            pass
    return ""

def fetch_doaj_subject(issn, title):
    """Extrai DOAJ Subject e Keywords para revistas Open Access."""
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
                        parts.append("DOAJ Subject: " + ", ".join(subjects))
                    if keywords:
                        parts.append("Keywords: " + ", ".join(keywords))
                    if parts:
                        return ". ".join(parts)
        except Exception:
            pass
    return ""

def fetch_openalex_details(issn, title):
    """Consulta OpenAlex para obter informações de escopo, tópicos e conceitos."""
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

                parts = []
                if desc and len(clean_text(desc)) > 20:
                    parts.append(clean_text(desc))
                elif topics:
                    parts.append("Topics: " + ", ".join(topics))
                elif concepts:
                    parts.append("Concepts: " + ", ".join(concepts))

                if parts:
                    return ". ".join(parts)
        except Exception:
            pass
    return ""

def scrape_homepage_profile(url):
    """Extrai Aims & Scope, Mission, About, Profile, Subject ou Description da Homepage."""
    if not url or str(url).strip() in ["-", "", "nan", "None"]:
        return "", "", ""

    url_str = str(url).strip()
    if not url_str.startswith("http"):
        url_str = "http://" + url_str

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }

    try:
        r = requests.get(url_str, headers=headers, timeout=5, verify=False, allow_redirects=True)
        if r.status_code != 200:
            return "", "", ""

        soup = BeautifulSoup(r.text, 'html.parser')

        escopo_text = ""
        missao_text = ""
        tipos_text = ""

        # 1. Missão Editorial
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

        # 2. Meta Description / Escopo
        meta = soup.find('meta', attrs={'name': re.compile(r'description', re.I)}) or soup.find('meta', property=re.compile(r'description', re.I))
        if meta and meta.get('content'):
            m_text = clean_text(meta.get('content'))
            if len(m_text) > 30 and not any(ign in m_text.lower() for ign in ["human", "captcha", "access denied", "robot"]):
                escopo_text = m_text[:600]

        # 3. OJS Summary / About Block / Focus & Scope
        if not escopo_text:
            ojs_div = soup.find('div', class_=re.compile(r'journal-summary|homepage-about|about|description|aims-and-scope|scope', re.I))
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
                if any(w in txt_low for w in ["publishes", "peer-reviewed", "scope", "aims to", "focuses on", "publica", "escopo", "editorial", "revista"]):
                    candidates.append(txt)
            if candidates:
                escopo_text = "\n\n".join(candidates[:2])[:600]

        return escopo_text, missao_text, tipos_text

    except Exception:
        pass
    return "", "", ""

def process_journal_profile(title, issn, homepage, known_map):
    """Orquestra o mapeamento de acordo com as instruções passo a passo do usuário."""
    t_clean = clean_text(title)
    t_norm = t_clean.lower()
    issn_clean = clean_text(issn).replace("-", "").lower()

    # 1. Verifica no mapa do catálogo unificado
    if t_norm in known_map:
        profile_pt = known_map[t_norm]
        profile_en = translate_to_academic_english(profile_pt)
        return profile_pt, profile_en
    if issn_clean and issn_clean in known_map:
        profile_pt = known_map[issn_clean]
        profile_en = translate_to_academic_english(profile_pt)
        return profile_pt, profile_en

    # 2. Se SAGE Publications: Description
    if homepage and "sagepub.com" in str(homepage).lower():
        sage_desc = fetch_sage_description(homepage, title)
        if sage_desc:
            profile_en = translate_to_academic_english(sage_desc)
            return sage_desc, profile_en

    # 3. Se Open Access: DOAJ Subject
    doaj_subj = fetch_doaj_subject(issn, title)
    
    # 4. Web Scraping da Homepage (Aims & Scope, Mission, About, Description)
    escopo, missao, tipos = scrape_homepage_profile(homepage)

    # 5. Fallback para OpenAlex API
    oa_info = ""
    if not escopo or len(escopo) < 20:
        oa_info = fetch_openalex_details(issn, title)

    # Monta a síntese estruturada
    parts = []
    if escopo:
        parts.append(f"Aims & Scope: {escopo}")
    elif sage_desc := fetch_sage_description(homepage, title):
        parts.append(f"Description: {sage_desc}")
    elif oa_info:
        parts.append(f"Aims & Scope: {oa_info}")

    if doaj_subj:
        parts.append(f"{doaj_subj}")
    if missao:
        parts.append(f"Mission: {missao}")
    if tipos:
        parts.append(f"Accepted Article Types: {tipos}")

    if not parts:
        return "Informação não encontrada", "Information not found"

    full_profile_pt = ". ".join(parts)
    full_profile_en = translate_to_academic_english(full_profile_pt)

    return full_profile_pt, full_profile_en

def process_row(idx, row, known_map):
    col_title = row.index[0]
    col_issn = row.index[1]
    col_hp = row.index[2]

    title = str(row.get(col_title, ""))
    issn = str(row.get(col_issn, ""))
    hp = str(row.get(col_hp, ""))

    pt_text, en_text = process_journal_profile(title, issn, hp, known_map)
    return idx, pt_text, en_text

def run_antigravity_enrichment(file_path="dados_Antigravity.csv", limit=None):
    if not os.path.exists(file_path):
        print(f"Arquivo {file_path} não encontrado.")
        return

    print(f"--- Iniciando Processamento de dados_Antigravity.csv ---")
    df = pd.read_csv(file_path, sep=';', encoding='utf-8-sig', low_memory=False)

    col_title = df.columns[0]
    col_issn = df.columns[1]
    col_hp = df.columns[2]
    col_scope = "Aims and Scope"
    col_trans = "Aims and Scope (translate)"

    if col_scope not in df.columns:
        df.insert(3, col_scope, "")
    if col_trans not in df.columns:
        df.insert(4, col_trans, "")

    df[col_scope] = df[col_scope].astype("object").fillna("").astype(str)
    df[col_trans] = df[col_trans].astype("object").fillna("").astype(str)

    known_map = build_known_catalog_map()

    mask_pending = df[col_scope].isna() | (df[col_scope].astype(str).str.strip() == "") | (df[col_scope].astype(str).str.strip() == "-")
    pending_indices = df[mask_pending].index.tolist()

    if limit:
        pending_indices = pending_indices[:limit]

    total = len(pending_indices)
    print(f"Total de periódicos a processar: {total}")

    if total == 0:
        print("Todos os periódicos de dados_Antigravity.csv já foram processados!")
        return

    success_count = 0
    start_time = time.time()

    for i in range(0, total, BATCH_SIZE):
        batch_indices = pending_indices[i:i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        total_batches = (total + BATCH_SIZE - 1) // BATCH_SIZE
        print(f"\n[Lote {batch_num}/{total_batches}] Processando periódicos {i+1} a {i+len(batch_indices)} de {total}...")

        batch_results = []
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {
                executor.submit(process_row, idx, df.iloc[idx], known_map): idx
                for idx in batch_indices
            }

            for future in as_completed(futures):
                idx = futures[future]
                try:
                    res_idx, pt_text, en_text = future.result()
                    batch_results.append((res_idx, pt_text, en_text))
                except Exception:
                    pass

        # Recarrega o CSV para gravação segura
        df_latest = pd.read_csv(file_path, sep=';', encoding='utf-8-sig', low_memory=False)
        df_latest[col_scope] = df_latest[col_scope].astype("object")
        df_latest[col_trans] = df_latest[col_trans].astype("object")
        for res_idx, pt_text, en_text in batch_results:
            df_latest.loc[res_idx, col_scope] = str(pt_text)
            df_latest.loc[res_idx, col_trans] = str(en_text)
            success_count += 1

        df_latest.to_csv(file_path, sep=';', index=False, encoding='utf-8-sig')

        elapsed = time.time() - start_time
        rate = (i + len(batch_indices)) / max(1, elapsed)
        rem_sec = (total - (i + len(batch_indices))) / max(0.1, rate)
        print(f"[OK] Lote {batch_num} salvo! +{len(batch_results)} processadas (Total: {success_count} | {elapsed/60:.1f} min decorridos | Est. restante: {rem_sec/60:.1f} min).")

    print(f"\n[FIM] Processamento de dados_Antigravity.csv concluído!")

if __name__ == "__main__":
    limit_val = int(sys.argv[1]) if len(sys.argv) > 1 else None
    run_antigravity_enrichment("dados_Antigravity.csv", limit=limit_val)

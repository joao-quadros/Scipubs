import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
import urllib.parse
import re
import os
import sys
import csv
import json
import urllib3
from concurrent.futures import ThreadPoolExecutor, as_completed

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuração de sys.stdout para UTF-8 no Windows
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

INPUT_FILE = "dados_parcial_2.csv"
OUTPUT_FILE = "dados_parcial_2_consolidado.csv"
WOS_FILE = "Web of Science 2025.csv"

MAX_WORKERS = 20
BATCH_SIZE = 100

class DSU:
    def __init__(self, n):
        self.parent = list(range(n))
    def find(self, i):
        path = []
        curr = i
        while self.parent[curr] != curr:
            path.append(curr)
            curr = self.parent[curr]
        for node in path:
            self.parent[node] = curr
        return curr
    def union(self, i, j):
        root_i = self.find(i)
        root_j = self.find(j)
        if root_i != root_j:
            self.parent[root_i] = root_j

def clean_title_str(x):
    if not x or pd.isna(x):
        return ""
    s = str(x).lower().strip()
    s = s.replace("&", " and ").replace(" et ", " and ")
    s = re.sub(r'[^a-z0-9]', '', s)
    return s

def clean_issn_str(x):
    if pd.isna(x):
        return ""
    return str(x).strip().replace("-", "").replace(" ", "").upper()

def clean_text(text):
    if not text:
        return ""
    text = re.sub(r'[\r\n\t]+', ' ', str(text))
    text = re.sub(r'\s+', ' ', text)
    text = text.replace('"', "'")
    text = re.sub(r'<[^>]+>', '', text)
    return text.strip()

def format_to_title_case(title):
    if not title or pd.isna(title):
        return ""
    return str(title).strip().title()

def translate_to_academic_english(text):
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

# ----------------- KNOWLEDGE BASE LOADING -----------------
KB_TITLE = {}
KB_ISSN = {}

def get_col_by_pattern(df, pattern):
    for c in df.columns:
        if pattern.lower() in str(c).lower():
            return c
    return None

def add_to_kb(df, title_pattern, issn_pattern, scope_pattern, trans_pattern=None):
    title_col = get_col_by_pattern(df, title_pattern)
    issn_col = get_col_by_pattern(df, issn_pattern)
    scope_col = get_col_by_pattern(df, scope_pattern)
    trans_col = get_col_by_pattern(df, trans_pattern) if trans_pattern else None

    if not title_col or not issn_col or not scope_col:
        return

    for _, r in df.iterrows():
        sc = str(r[scope_col]).strip() if pd.notna(r[scope_col]) else ''
        tr = str(r[trans_col]).strip() if trans_col and pd.notna(r[trans_col]) else ''
        if len(sc) > 20 and 'não encontrada' not in sc.lower():
            t_clean = clean_title_str(r[title_col])
            i_clean = clean_issn_str(r[issn_col])
            if t_clean:
                KB_TITLE[t_clean] = (sc, tr)
            if i_clean:
                KB_ISSN[i_clean] = (sc, tr)

def load_all_kbs():
    print("--- Inicializando Base de Conhecimento Local ---")
    
    # 1. Web of Science 2025.csv (dados em inglês fresquinhos!)
    if os.path.exists("Web of Science 2025.csv"):
        try:
            df = pd.read_csv("Web of Science 2025.csv")
            add_to_kb(df, 'Journal title', 'ISSN', 'Aims and Scope', 'Aims and Scope (translate)')
        except Exception as e:
            print("Erro ao carregar Web of Science 2025.csv no KB:", e)

    # 2. dados_Antigravity_novo.csv
    if os.path.exists("dados_Antigravity_novo.csv"):
        try:
            df = pd.read_csv("dados_Antigravity_novo.csv", sep=';', encoding='utf-8-sig', on_bad_lines='skip', low_memory=False)
            add_to_kb(df, 'tulo', 'issn', 'Scope: ', 'Scope (translate)')
        except Exception as e:
            print("Erro ao carregar dados_Antigravity_novo.csv no KB:", e)

    # 3. dados_new_atualizado.csv
    if os.path.exists("dados_new_atualizado.csv"):
        try:
            df = pd.read_csv("dados_new_atualizado.csv", sep=';', encoding='utf-8-sig', on_bad_lines='skip', low_memory=False)
            add_to_kb(df, 'tulo', 'issn', 'Scope', 'Scope (translate)')
        except Exception as e:
            print("Erro ao carregar dados_new_atualizado.csv no KB:", e)

    # 4. dados_2.csv
    if os.path.exists("dados_2.csv"):
        try:
            df = pd.read_csv("dados_2.csv", sep=';', encoding='utf-8-sig', on_bad_lines='skip', low_memory=False)
            add_to_kb(df, df.columns[0], df.columns[1], df.columns[3])
        except Exception as e:
            print("Erro ao carregar dados_2.csv no KB:", e)

    print(f"Base de Conhecimento carregada: {len(KB_TITLE)} títulos e {len(KB_ISSN)} ISSNs.")

# -----------------------------------------------------------

def fetch_journal_scope_multi_source(session, title, issn=None):
    t_clean = normalize_journal_title(title)
    if not t_clean:
        return ""

    # Wikipedia
    try:
        url_wiki = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(t_clean)}&format=json&utf8="
        r = session.get(url_wiki, headers=WIKI_HEADERS, timeout=4)
        if r.status_code == 200:
            results = r.json().get("query", {}).get("search", [])
            for res in results[:2]:
                snippet = res.get("snippet", "")
                title_wiki = res.get("title", "")
                if len(snippet) > 35:
                    return f"Aims and Scope: {clean_text(snippet)}"
    except Exception:
        pass

    # Crossref
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

    return ""

def normalize_journal_title(title):
    if not title or str(title).strip() in ["-", "", "nan", "None"]:
        return ""
    t = str(title).strip()
    if t.isupper():
        t = t.title()
    t = re.sub(r'\(.*?\)', '', t).strip()
    t = re.sub(r'[^a-zA-Z0-9\s\&\-\:]', '', t).strip()
    return t

def process_row_scope(session, idx, row):
    col_title = row.index[1]
    col_issn = row.index[2]

    title = str(row.get(col_title, ""))
    issn = str(row.get(col_issn, ""))

    clean_t = clean_title_str(title)
    clean_i = clean_issn_str(issn)

    # 1. Verifica KB local primeiro
    if clean_i and clean_i in KB_ISSN:
        sc, tr = KB_ISSN[clean_i]
        # Dá preferência para o escopo em inglês
        best_scope = tr if tr and len(tr) > 20 else sc
        if len(best_scope) > 20:
            return idx, clean_text(best_scope)

    if clean_t and clean_t in KB_TITLE:
        sc, tr = KB_TITLE[clean_t]
        best_scope = tr if tr and len(tr) > 20 else sc
        if len(best_scope) > 20:
            return idx, clean_text(best_scope)

    # 2. Busca ativa se necessário
    snippet_text = fetch_journal_scope_multi_source(session, title, issn)
    if not snippet_text or len(snippet_text) < 15:
        scope_en = ""
    else:
        scope_en = translate_to_academic_english(snippet_text)

    return idx, scope_en

def choose_best_title(titles):
    valid_titles = [str(t).strip() for t in titles if pd.notna(t) and str(t).strip() not in ["", "-", "nan"]]
    if not valid_titles:
        return ""
    mixed_case = [t for t in valid_titles if not t.isupper() and any(c.islower() for c in t)]
    if mixed_case:
        return max(mixed_case, key=len)
    return max(valid_titles, key=len)

def merge_issns(issns):
    valid = []
    seen = set()
    for val in issns:
        if pd.isna(val):
            continue
        v_str = str(val).strip()
        if v_str and v_str not in ["", "-", "nan"] and v_str.lower() not in seen:
            valid.append(v_str)
            seen.add(v_str.lower())
    return ", ".join(valid)

def merge_categorical_field(series):
    unique_vals = set()
    for val in series:
        if pd.isna(val):
            continue
        val_str = str(val).strip()
        if val_str and val_str not in ["", "-", "nan"]:
            for part in val_str.split(","):
                part_clean = part.strip()
                if part_clean and part_clean not in ["", "-", "nan"]:
                    unique_vals.add(part_clean)
    if not unique_vals:
        return ""
    return ", ".join(sorted(list(unique_vals)))

def max_numeric(series):
    nums = []
    for val in series:
        if pd.notna(val):
            val_str = str(val).strip()
            # Se for uma URL (caso do índice h5), ignora
            if val_str.startswith("http"):
                continue
            try:
                nums.append(float(val_str.replace(",", ".").strip()))
            except ValueError:
                pass
    return max(nums) if nums else np.nan

def first_non_null(series):
    for val in series:
        if pd.notna(val) and str(val).strip() not in ["", "-", "nan"]:
            return val
    return np.nan

def run_pipeline():
    load_all_kbs()

    if not os.path.exists(INPUT_FILE):
        print(f"Erro: {INPUT_FILE} não encontrado.")
        return

    # Load Web of Science 2025.csv mapping
    wos_title_map = {}
    wos_issn_map = {}
    if os.path.exists(WOS_FILE):
        print(f"Carregando mapeamento de indexadores de {WOS_FILE}...")
        df_wos = pd.read_csv(WOS_FILE)
        for _, r in df_wos.iterrows():
            idx_val = str(r['Indexador']).strip()
            t = clean_title_str(r['Journal title'])
            iss = clean_issn_str(r['ISSN'])
            if t:
                wos_title_map[t] = idx_val
            if iss:
                wos_issn_map[iss] = idx_val

    print(f"Lendo {INPUT_FILE}...")
    df = pd.read_csv(INPUT_FILE, sep=',', encoding='latin-1', low_memory=False)
    print(f"Linhas originais carregadas: {len(df)}")

    # 1. Substituição de WoS por indexadores específicos
    print("Mapeando indexadores específicos do Web of Science...")
    for idx, row in df.iterrows():
        idx_val = str(row.get('Indexador', '')).strip()
        if "WoS" in idx_val:
            title = row.get('Título da Revista', '')
            issn = row.get('ISSN', '')
            
            clean_t = clean_title_str(title)
            clean_i = clean_issn_str(issn)
            
            specific_wos = ""
            if clean_i and clean_i in wos_issn_map:
                specific_wos = wos_issn_map[clean_i]
            elif clean_t and clean_t in wos_title_map:
                specific_wos = wos_title_map[clean_t]
            else:
                # Fallback se não bater na planilha de 2025
                jif = row.get('JIF')
                if pd.notna(jif) and str(jif).strip() not in ["", "-", "nan"]:
                    specific_wos = "Web of Science - SCIE"
                else:
                    specific_wos = "Web of Science - ESCI"

            # Mescla com outros indexadores (Scopus, etc.)
            other_indexers = [part.strip() for part in idx_val.split(",") if part.strip() != "WoS"]
            if specific_wos:
                for part in specific_wos.split(","):
                    other_indexers.append(part.strip())
            
            # Deduplica e ordena
            unique_idx = sorted(list(set([x for x in other_indexers if x])))
            df.at[idx, 'Indexador'] = ", ".join(unique_idx)

    # 2. Mineração e Tradução de Escopos em Inglês
    print("Processando escopos ('Aims and Scope') em Inglês...")
    df['Aims and Scope'] = df['Aims and Scope'].astype("object").fillna("").astype(str)
    
    mask_pending = df['Aims and Scope'].isna() | (df['Aims and Scope'].astype(str).str.strip() == "") | (df['Aims and Scope'].astype(str).str.strip() == "-")
    pending_indices = df[mask_pending].index.tolist()
    
    print(f"Linhas pendentes de escopo: {len(pending_indices)}")

    if len(pending_indices) > 0:
        sessions = [requests.Session() for _ in range(MAX_WORKERS)]
        success_count = 0
        for i in range(0, len(pending_indices), BATCH_SIZE):
            batch_indices = pending_indices[i:i + BATCH_SIZE]
            
            batch_results = []
            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                futures = {}
                for j, b_idx in enumerate(batch_indices):
                    session = sessions[j % MAX_WORKERS]
                    futures[executor.submit(process_row_scope, session, b_idx, df.iloc[b_idx])] = b_idx

                for future in as_completed(futures):
                    b_idx = futures[future]
                    try:
                        res_idx, en_scope = future.result()
                        batch_results.append((res_idx, en_scope))
                    except Exception:
                        pass

            for res_idx, en_scope in batch_results:
                df.at[res_idx, 'Aims and Scope'] = clean_text(en_scope)
                if en_scope:
                    success_count += 1
            print(f"Lote escopo {(i // BATCH_SIZE)+1} salvo! {i+len(batch_indices)} processadas (+{success_count} escopos obtidos).")

    # 3. Consolidação e Deduplicação (Connected Components)
    print("Iniciando agrupamento e consolidação de duplicados (DSU)...")
    df['clean_issn'] = df['ISSN'].apply(clean_issn_str)
    df['clean_title'] = df['Título da Revista'].apply(clean_title_str)

    n_rows = len(df)
    dsu = DSU(n_rows)
    
    issn_to_idx = {}
    title_to_idx = {}

    for idx in range(n_rows):
        c_issn = df.iloc[idx]['clean_issn']
        c_title = df.iloc[idx]['clean_title']

        if c_issn:
            if c_issn in issn_to_idx:
                dsu.union(idx, issn_to_idx[c_issn])
            else:
                issn_to_idx[c_issn] = idx

        if c_title:
            if c_title in title_to_idx:
                dsu.union(idx, title_to_idx[c_title])
            else:
                title_to_idx[c_title] = idx

    df['group_root'] = [dsu.find(i) for i in range(n_rows)]
    grouped = df.groupby('group_root')
    print(f"Total de revistas únicas após consolidação: {grouped.ngroups}")

    consolidated_rows = []

    for root, group in grouped:
        row_data = {}
        
        # Título
        row_data['Título da Revista'] = choose_best_title(group['Título da Revista'])
        
        # ISSN
        row_data['ISSN'] = merge_issns(group['ISSN'])
        
        # Homepage
        row_data['Homepage'] = first_non_null(group['Homepage'])
        if pd.isna(row_data['Homepage']):
            row_data['Homepage'] = ""

        # Aims and Scope (Escolhe o maior escopo em inglês)
        scopes = [str(s).strip() for s in group['Aims and Scope'] if pd.notna(s) and str(s).strip() not in ["", "-", "nan"]]
        row_data['Aims and Scope'] = max(scopes, key=len) if scopes else ""

        # Categóricos
        row_data['Grande Area'] = merge_categorical_field(group['Grande Area'])
        row_data['Area do Conhecimento'] = merge_categorical_field(group['Area do Conhecimento'])
        row_data['Categoria'] = merge_categorical_field(group['Categoria'])
        row_data['Indexador'] = merge_categorical_field(group['Indexador'])

        # Métricas
        row_data['JIF'] = max_numeric(group['JIF'])
        row_data['Quartil JCR'] = merge_categorical_field(group['Quartil JCR'])
        row_data['SJR'] = max_numeric(group['SJR'])
        row_data['SJR Best Quartile'] = merge_categorical_field(group['SJR Best Quartile'])
        row_data['H index'] = max_numeric(group['H index'])
        
        # O índice h5 pode vir como URL ou número, preserva primeiro não-nulo ou max
        h5_vals = [str(x).strip() for x in group['Índice h5'] if pd.notna(x) and str(x).strip() not in ["", "-", "nan"]]
        row_data['Índice h5'] = h5_vals[0] if h5_vals else ""

        consolidated_rows.append(row_data)

    df_consolidated = pd.DataFrame(consolidated_rows)

    # Ordena alfabeticamente
    df_consolidated['sort_key'] = df_consolidated['Título da Revista'].apply(clean_title_str)
    df_consolidated = df_consolidated.sort_values(by='sort_key').drop(columns=['sort_key'])

    # Adiciona numeração N
    df_consolidated.insert(0, 'N', [float(i + 1) for i in range(len(df_consolidated))])

    # Gravação do arquivo final consolidado com codificação robusta e aspas de proteção
    df_consolidated.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig', quoting=csv.QUOTE_ALL)
    print(f"Salvo arquivo consolidado: {OUTPUT_FILE}")

    df_consolidated.to_csv(INPUT_FILE, index=False, encoding='utf-8-sig', quoting=csv.QUOTE_ALL)
    print(f"Sobrescrito arquivo original para atualização: {INPUT_FILE}")

if __name__ == "__main__":
    run_pipeline()

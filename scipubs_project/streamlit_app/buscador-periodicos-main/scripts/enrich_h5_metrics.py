import pandas as pd
import requests
from bs4 import BeautifulSoup
import os
import re
import time
import sys
import urllib.parse
from difflib import SequenceMatcher
from concurrent.futures import ThreadPoolExecutor, as_completed

MAX_WORKERS = 10  # Respeita o limite do Scholar para evitar capchas de IP
TIMEOUT = 6
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

def fetch_h5_from_scholar(journal_title):
    """Consulta o Google Scholar Venues Search e extrai o h5-index e h5-median."""
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
        r = requests.get(url_gs, headers=headers, timeout=TIMEOUT)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            table = soup.find('table', id='gsc_mp_table') or soup.find('table')
            if table:
                rows = table.find_all('tr')
                for tr in rows[1:]:  # Pula o cabeçalho
                    tds = [td.text.strip() for td in tr.find_all(['td', 'th'])]
                    if len(tds) >= 4:
                        pub_name = tds[1]
                        h5_idx = tds[2]
                        h5_med = tds[3]
                        
                        # Verifica a similaridade do nome da revista
                        score = SequenceMatcher(None, title_norm, normalizar(pub_name)).ratio()
                        if score >= 0.75:
                            return h5_idx, h5_med
    except Exception:
        pass
    return "", ""

def process_row_h5(idx, title):
    h5_idx, h5_med = fetch_h5_from_scholar(title)
    return idx, h5_idx, h5_med

def run_h5_enrichment(file_path="dados_2.csv", limit=None):
    if not os.path.exists(file_path):
        print(f"Arquivo {file_path} não encontrado.")
        return

    print(f"--- Iniciando enriquecimento de Índice h5 e Mediana h5 em {file_path} ---")
    df = pd.read_csv(file_path, sep=';', encoding='utf-8-sig', low_memory=False)

    col_title = df.columns[0]
    col_h5_idx = "Índice h5"
    col_h5_med = "Mediana h5"

    if col_h5_idx not in df.columns:
        df[col_h5_idx] = ""
    if col_h5_med not in df.columns:
        # Insere a coluna Mediana h5 logo após Índice h5
        idx_h5 = df.columns.get_loc(col_h5_idx)
        df.insert(idx_h5 + 1, col_h5_med, "")

    df[col_h5_idx] = df[col_h5_idx].astype(object).fillna("").astype(str)
    df[col_h5_med] = df[col_h5_med].astype(object).fillna("").astype(str)

    # Filtra revistas onde Índice h5 ou Mediana h5 estão vazios
    mask_empty = (df[col_h5_idx].isna() | (df[col_h5_idx].astype(str).str.strip() == "") | (df[col_h5_idx].astype(str).str.strip() == "-")) | \
                 (df[col_h5_med].isna() | (df[col_h5_med].astype(str).str.strip() == "") | (df[col_h5_med].astype(str).str.strip() == "-"))
    
    indices = df[mask_empty].index.tolist()

    if limit:
        indices = indices[:limit]

    total = len(indices)
    print(f"Total de revistas para pesquisar h5 metrics: {total}")

    success_count = 0
    start_time = time.time()

    for i in range(0, total, BATCH_SIZE):
        batch_indices = indices[i:i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        total_batches = (total + BATCH_SIZE - 1) // BATCH_SIZE
        print(f"\n[Lote {batch_num}/{total_batches}] Consultando Métricas h5 para itens {i+1} a {i+len(batch_indices)}...")

        batch_success = 0
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {
                executor.submit(process_row_h5, idx, str(df.loc[idx, col_title])): idx
                for idx in batch_indices
            }

            for future in as_completed(futures):
                idx = futures[future]
                try:
                    res_idx, h5_idx, h5_med = future.result()
                    if h5_idx or h5_med:
                        if h5_idx: df.at[res_idx, col_h5_idx] = str(h5_idx)
                        if h5_med: df.at[res_idx, col_h5_med] = str(h5_med)
                        batch_success += 1
                        success_count += 1
                except Exception as ex:
                    pass

        # Salva o progresso
        try:
            df.to_csv(file_path, sep=';', index=False, encoding='utf-8-sig')
            elapsed = time.time() - start_time
            print(f"[OK] Lote {batch_num} salvo! +{batch_success} revistas com Métricas h5 atualizadas (Total: {success_count} | {elapsed:.1f}s decorridos).")
        except Exception as e:
            print(f"Erro ao salvar: {e}")

    print(f"\n[FIM] Concluído! Total de {success_count} revistas enriquecidas com Índice h5 e Mediana h5 em {file_path}.")

if __name__ == "__main__":
    limit_val = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    run_h5_enrichment("dados_2.csv", limit=limit_val)

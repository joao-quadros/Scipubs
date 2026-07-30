import pandas as pd
import requests
import urllib.parse
import os
import re
import time
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

MAX_WORKERS = 25  # 25 conexões simultâneas de tradução
BATCH_SIZE = 100  # Salva no CSV a cada 100 itens traduzidos

def clean_text(text):
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', str(text))
    return text.strip()

def translate_to_academic_english(text):
    """Traduz textos em português/espanhol/outros idiomas para Inglês Acadêmico via Google GTX API."""
    if not text or str(text).strip() in ["-", "", "nan", "None"]:
        return ""
        
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

def process_translation_row(idx, src_text):
    trans_text = translate_to_academic_english(src_text)
    return idx, trans_text

def run_translation(file_path="dados_complemento.csv", limit=None):
    if not os.path.exists(file_path):
        print(f"Arquivo {file_path} não encontrado.")
        return

    print(f"--- Iniciando Tradução Automatizada para Inglês Acadêmico em {file_path} ---")
    df = pd.read_csv(file_path, sep=';', encoding='utf-8-sig', low_memory=False)

    col_src = "Aims and Scope"
    col_dst = "Aims and Scope (translate)"

    if col_dst not in df.columns:
        idx_src = df.columns.get_loc(col_src) if col_src in df.columns else 3
        df.insert(idx_src + 1, col_dst, "")

    df[col_src] = df[col_src].astype(object).fillna("").astype(str)
    df[col_dst] = df[col_dst].astype(object).fillna("").astype(str)

    # Filtra linhas onde Aims and Scope está preenchido mas Aims and Scope (translate) está vazio
    mask_has_src = df[col_src].notna() & (df[col_src].astype(str).str.strip() != "") & (df[col_src].astype(str).str.strip() != "-")
    mask_empty_dst = df[col_dst].isna() | (df[col_dst].astype(str).str.strip() == "") | (df[col_dst].astype(str).str.strip() == "-")

    indices = df[mask_has_src & mask_empty_dst].index.tolist()

    if limit:
        indices = indices[:limit]

    total = len(indices)
    print(f"Total de revistas a traduzir nesta rodada: {total}")

    if total == 0:
        print("Todas as revistas já foram traduzidas!")
        return

    success_count = 0
    start_time = time.time()

    for i in range(0, total, BATCH_SIZE):
        batch_indices = indices[i:i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        total_batches = (total + BATCH_SIZE - 1) // BATCH_SIZE
        print(f"\n[Lote {batch_num}/{total_batches}] Traduzindo revistas {i+1} a {i+len(batch_indices)} de {total}...")

        batch_results = []
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {
                executor.submit(process_translation_row, idx, str(df.loc[idx, col_src])): idx
                for idx in batch_indices
            }

            for future in as_completed(futures):
                idx = futures[future]
                try:
                    res_idx, trans_text = future.result()
                    if trans_text:
                        batch_results.append((res_idx, trans_text))
                except Exception:
                    pass

        # Recarrega o CSV para gravação segura
        df_latest = pd.read_csv(file_path, sep=';', encoding='utf-8-sig', low_memory=False)
        if col_dst not in df_latest.columns:
            idx_src = df_latest.columns.get_loc(col_src) if col_src in df_latest.columns else 3
            df_latest.insert(idx_src + 1, col_dst, "")

        df_latest[col_dst] = df_latest[col_dst].astype(object).fillna("").astype(str)

        batch_success = 0
        for res_idx, trans_text in batch_results:
            df_latest.at[res_idx, col_dst] = str(trans_text)
            batch_success += 1
            success_count += 1

        df_latest.to_csv(file_path, sep=';', index=False, encoding='utf-8-sig')
        elapsed = time.time() - start_time
        rate = (i + len(batch_indices)) / max(1, elapsed)
        rem_sec = (total - (i + len(batch_indices))) / max(0.1, rate)
        print(f"[OK] Lote {batch_num} salvo! +{batch_success} traduzidas (Total acumulado: {success_count} | {elapsed/60:.1f} min decorridos | Previsao restante: {rem_sec/60:.1f} min).")

    print(f"\n[FIM] Tradução concluída! Total de {success_count} revistas traduzidas em {file_path}.")

if __name__ == "__main__":
    limit_val = int(sys.argv[1]) if len(sys.argv) > 1 else None
    run_translation("dados_complemento.csv", limit=limit_val)

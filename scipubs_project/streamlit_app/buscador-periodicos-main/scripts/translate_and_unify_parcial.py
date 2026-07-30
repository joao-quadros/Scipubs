import pandas as pd
import numpy as np
import urllib.parse
import requests
import re
import os
import sys
import csv
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Garante que sys.stdout use UTF-8 no Windows
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

INPUT_FILE = "dados_parcial_2.csv"
OUTPUT_FILE = "dados_parcial_2_traduzido.csv"
WOS_FILE = "Web of Science 2025.csv"

MAX_WORKERS = 30  # 30 threads para tradução paralela ultra rápida

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

def format_issn(issn_raw):
    """Formata o ISSN para o padrão XXXX-XXXX se tiver 8 caracteres, caso contrário limpa e retorna."""
    if not issn_raw or pd.isna(issn_raw):
        return ""
    s = str(issn_raw).strip().replace("-", "").replace(" ", "").upper()
    if len(s) == 8:
        return f"{s[:4]}-{s[4:]}"
    return str(issn_raw).strip()

def translate_term(term):
    """Traduz termos específicos para Inglês Acadêmico."""
    if not term or pd.isna(term) or str(term).strip() in ["", "-", "nan", "None"]:
        return ""

    term_clean = str(term).strip()
    
    # Dicionário de tradução manual para termos estritamente comuns de Grande Área
    manual_translations = {
        "ciências da saúde": "Health Sciences",
        "ciencias da saude": "Health Sciences",
        "engenharias": "Engineering",
        "ciências exatas e da terra": "Exact and Earth Sciences",
        "ciencias exatas e da terra": "Exact and Earth Sciences",
        "ciências sociais aplicadas": "Applied Social Sciences",
        "ciencias sociais aplicadas": "Applied Social Sciences",
        "ciências humanas": "Humanities",
        "ciencias humanas": "Humanities",
        "linguística, letras e artes": "Linguistics, Literature and Arts",
        "linguistica, letras e artes": "Linguistics, Literature and Arts",
        "ciências biológicas": "Biological Sciences",
        "ciencias biologicas": "Biological Sciences",
        "ciências agrárias": "Agricultural Sciences",
        "ciencias agrarias": "Agricultural Sciences",
        "multidisciplinar": "Multidisciplinary",
        "outras / não classificado": "Others / Unclassified",
        "outras / nao classificado": "Others / Unclassified",
        "outras": "Others"
    }

    term_lower = term_clean.lower()
    if term_lower in manual_translations:
        return manual_translations[term_lower]

    # Chamada automática via Google GTX para outros termos
    try:
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=pt&tl=en&dt=t&q={urllib.parse.quote(term_clean)}"
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            res_json = r.json()
            translated = "".join([s[0] for s in res_json[0] if s and len(s) > 0 and s[0]])
            if translated:
                return translated.strip().title()
    except Exception:
        pass
    return term_clean.title()

def run_translation_pipeline():
    if not os.path.exists(INPUT_FILE):
        print(f"Erro: {INPUT_FILE} não encontrado.")
        return

    # 1. Carrega mapeamento WoS 2025 para unificação de ISSN
    wos_issn_map = {}
    if os.path.exists(WOS_FILE):
        print("Carregando base da Web of Science 2025 para cruzamento de ISSN...")
        df_wos = pd.read_csv(WOS_FILE)
        for _, r in df_wos.iterrows():
            t = clean_title_str(r['Journal title'])
            iss = format_issn(r['ISSN'])
            if t and iss:
                wos_issn_map[t] = iss

    print(f"Lendo {INPUT_FILE}...")
    df = pd.read_csv(INPUT_FILE, sep=',', encoding='utf-8-sig', low_memory=False)
    print(f"Total de registros: {len(df)}")

    # 2. Unificação de ISSN (Utilizando o de maior evidência)
    print("Unificando ISSNs...")
    for idx, row in df.iterrows():
        issn_val = str(row.get('ISSN', '')).strip()
        if not issn_val or issn_val == "nan":
            continue

        parts = [p.strip() for p in issn_val.split(",") if p.strip()]
        if len(parts) > 1:
            title_clean = clean_title_str(row.get('Título da Revista', ''))
            
            # Tenta encontrar o ISSN na planilha oficial da WoS 2025
            best_issn = ""
            if title_clean in wos_issn_map:
                best_issn = wos_issn_map[title_clean]
            
            # Se não estiver no WoS 2025, escolhe o primeiro da lista (maior evidência primária)
            if not best_issn:
                best_issn = format_issn(parts[0])
            
            df.at[idx, 'ISSN'] = best_issn
        else:
            df.at[idx, 'ISSN'] = format_issn(parts[0])

    # 3. Coleta de termos para tradução
    print("Coletando termos de Grande Área, Área do Conhecimento e Categoria...")
    
    unique_terms = set()
    
    # Grande Área
    for val in df['Grande Area'].dropna():
        for part in str(val).split(","):
            part_clean = part.strip()
            if part_clean and part_clean not in ["", "-", "nan"]:
                unique_terms.add(part_clean)

    # Área do Conhecimento
    for val in df['Area do Conhecimento'].dropna():
        for part in str(val).split(","):
            part_clean = part.strip()
            if part_clean and part_clean not in ["", "-", "nan"]:
                unique_terms.add(part_clean)

    # Categoria
    for val in df['Categoria'].dropna():
        for part in str(val).split(","):
            part_clean = part.strip()
            if part_clean and part_clean not in ["", "-", "nan"]:
                unique_terms.add(part_clean)

    print(f"Total de termos únicos coletados para tradução: {len(unique_terms)}")

    # Tradução em lote com Threads
    translation_cache = {}
    print("Iniciando tradução paralela via Google GTX API...")
    
    start_time = time.time()
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(translate_term, term): term for term in unique_terms}
        for future in as_completed(futures):
            term = futures[future]
            try:
                trans = future.result()
                translation_cache[term] = trans
            except Exception:
                translation_cache[term] = term

    print(f"Tradução paralela concluída em {time.time() - start_time:.1f} segundos!")

    # 4. Mapeamento dos termos traduzidos de volta no DataFrame
    print("Mapeando traduções no DataFrame...")
    
    def map_translation_list(val):
        if pd.isna(val):
            return ""
        translated_parts = []
        for part in str(val).split(","):
            part_clean = part.strip()
            if part_clean in translation_cache:
                translated_parts.append(translation_cache[part_clean])
            else:
                translated_parts.append(part_clean)
        # Remove duplicados mantendo a ordem
        seen = set()
        dedup_parts = []
        for p in translated_parts:
            if p.lower() not in seen:
                dedup_parts.append(p)
                seen.add(p.lower())
        return ", ".join(dedup_parts)

    df['Grande Area'] = df['Grande Area'].apply(map_translation_list)
    df['Area do Conhecimento'] = df['Area do Conhecimento'].apply(map_translation_list)
    df['Categoria'] = df['Categoria'].apply(map_translation_list)

    # 5. Gravação final com codificação utf-8-sig e quoting total
    df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig', quoting=csv.QUOTE_ALL)
    print(f"Salvo arquivo traduzido: {OUTPUT_FILE}")

    df.to_csv(INPUT_FILE, index=False, encoding='utf-8-sig', quoting=csv.QUOTE_ALL)
    print(f"Sobrescrito arquivo original para atualização: {INPUT_FILE}")

if __name__ == "__main__":
    run_translation_pipeline()

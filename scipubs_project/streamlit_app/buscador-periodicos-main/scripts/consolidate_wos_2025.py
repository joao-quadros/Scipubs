import pandas as pd
import numpy as np
import re
import os
import sys

# Garante que sys.stdout use UTF-8 no Windows
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

INPUT_FILE = "Web of Science 2025.csv"
OUTPUT_FILE = "Web of Science 2025_consolidado.csv"

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

def clean_issn_str(x):
    if pd.isna(x):
        return ""
    return str(x).strip().replace("-", "").replace(" ", "").upper()

def clean_title_str(x):
    if pd.isna(x):
        return ""
    s = str(x).lower().strip()
    s = s.replace("&", " and ").replace(" et ", " and ")
    s = re.sub(r'[^a-z0-9]', '', s)
    return s

def format_to_title_case(title):
    """Padroniza o título com apenas as iniciais de cada termo em maiúsculo (Title Case)."""
    if not title or pd.isna(title):
        return ""
    # Converte para Title Case
    t = str(title).strip().title()
    # Corrige alguns padrões menores se necessário, mas o principal é capitalizar iniciais
    return t

def merge_categories(categories_list):
    """
    Na coluna D 'Categorias', altera a barra (|) por vírgula (,),
    deduplica os termos e une-os de volta com vírgula e espaço.
    """
    unique_cats = []
    seen = set()
    for cat_val in categories_list:
        if pd.isna(cat_val):
            continue
        # Altera a barra (|) por vírgula (,)
        val_replaced = str(cat_val).replace("|", ",")
        # Quebra pelos delimitadores de vírgula
        for part in val_replaced.split(","):
            part_clean = part.strip()
            if part_clean and part_clean not in ["", "-", "nan"] and part_clean.lower() not in seen:
                unique_cats.append(part_clean)
                seen.add(part_clean.lower())
    return ", ".join(unique_cats)

def merge_indexers(indexers_list):
    """
    Une todos os indexadores do grupo sem repetição, separados por vírgula e espaço,
    mantendo-os ordenados alfabeticamente.
    """
    unique_idxs = set()
    for idx_val in indexers_list:
        if pd.isna(idx_val):
            continue
        for part in str(idx_val).split(","):
            part_clean = part.strip()
            if part_clean and part_clean not in ["", "-", "nan"]:
                unique_idxs.add(part_clean)
    return ", ".join(sorted(list(unique_idxs)))

def run_wos_consolidation():
    if not os.path.exists(INPUT_FILE):
        print(f"Erro: Arquivo {INPUT_FILE} não encontrado.")
        return

    print(f"--- Carregando {INPUT_FILE} ---")
    df = pd.read_csv(INPUT_FILE, sep=',')
    print(f"Total de linhas originais: {len(df)}")

    # Onde não houver ISSN, insere a informação do eISSN
    mask_no_issn = df['ISSN'].isna() | (df['ISSN'].astype(str).str.strip() == "") | (df['ISSN'].astype(str).str.strip() == "-")
    df.loc[mask_no_issn, 'ISSN'] = df.loc[mask_no_issn, 'eISSN']

    # Pré-processa chaves de agrupamento
    df['clean_issn'] = df['ISSN'].apply(clean_issn_str)
    df['clean_title'] = df['Journal title'].apply(clean_title_str)

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

    # Mapeia cada linha para seu representante DSU
    df['group_root'] = [dsu.find(i) for i in range(n_rows)]
    
    grouped = df.groupby('group_root')
    print(f"Número de revistas únicas após consolidação: {grouped.ngroups}")

    consolidated_rows = []

    for root, group in grouped:
        row_data = {}
        
        # Título da revista (Padroniza com iniciais em maiúsculo - Title Case)
        raw_titles = [str(t).strip() for t in group['Journal title'] if pd.notna(t)]
        best_raw_title = max(raw_titles, key=len) if raw_titles else ""
        row_data['Journal title'] = format_to_title_case(best_raw_title)

        # ISSN e eISSN
        issns = [str(x).strip() for x in group['ISSN'] if pd.notna(x) and str(x).strip() not in ["", "-", "nan"]]
        row_data['ISSN'] = issns[0] if issns else ""

        eissns = [str(x).strip() for x in group['eISSN'] if pd.notna(x) and str(x).strip() not in ["", "-", "nan"]]
        row_data['eISSN'] = eissns[0] if eissns else ""

        # Categorias (Altera barra | por vírgula e deduplica)
        row_data['Categorias'] = merge_categories(group['Categorias'])

        # Indexadores (Separa todos com vírgula e espaço)
        row_data['Indexador'] = merge_indexers(group['Indexador'])

        consolidated_rows.append(row_data)

    df_consolidated = pd.DataFrame(consolidated_rows)

    # Ordena alfabeticamente pelo título
    df_consolidated['sort_key'] = df_consolidated['Journal title'].apply(clean_title_str)
    df_consolidated = df_consolidated.sort_values(by='sort_key').drop(columns=['sort_key'])

    # Salva os resultados nos arquivos CSV
    df_consolidated.to_csv(OUTPUT_FILE, index=False, encoding='utf-8')
    print(f"Salvo arquivo consolidado: {OUTPUT_FILE}")

    df_consolidated.to_csv(INPUT_FILE, index=False, encoding='utf-8')
    print(f"Sobrescrito arquivo original para atualização: {INPUT_FILE}")

if __name__ == "__main__":
    run_wos_consolidation()

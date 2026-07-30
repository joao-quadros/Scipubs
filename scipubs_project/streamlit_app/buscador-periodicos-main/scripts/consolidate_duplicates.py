import pandas as pd
import numpy as np
import re
import os
import sys

# Garante que sys.stdout use UTF-8 no Windows
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

INPUT_FILE = "dados_teste.xlsx"
OUTPUT_FILE = "dados_teste_consolidado.xlsx"

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

def clean_issn(x):
    if pd.isna(x):
        return ""
    return str(x).strip().replace("-", "").replace(" ", "").upper()

def clean_title(x):
    if pd.isna(x):
        return ""
    s = str(x).lower().strip()
    s = s.replace("&", " and ").replace(" et ", " and ")
    s = re.sub(r'[^a-z0-9]', '', s)
    return s

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

def merge_indexers(indexers):
    """
    Na coluna I (Indexador) deve aparecer apenas os indexadores Web of Science ou Scopus.
    Se uma revista possuir os dois, utilize Web of Science, Scopus.
    """
    has_wos = False
    has_scopus = False
    for idx in indexers:
        if pd.isna(idx):
            continue
        idx_str = str(idx).lower()
        if "web of science" in idx_str or "wos" in idx_str:
            has_wos = True
        if "scopus" in idx_str:
            has_scopus = True
            
    if has_wos and has_scopus:
        return "Web of Science, Scopus"
    elif has_wos:
        return "Web of Science"
    elif has_scopus:
        return "Scopus"
    return ""

def merge_categorical_field(series):
    """
    Deduplica e mescla campos textuais categóricos com vírgula e espaço,
    ordenados alfabeticamente.
    """
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

def first_non_null(series):
    for val in series:
        if pd.notna(val) and str(val).strip() not in ["", "-", "nan"]:
            return val
    return np.nan

def max_numeric(series):
    nums = []
    for val in series:
        if pd.notna(val):
            try:
                nums.append(float(str(val).replace(",", ".").strip()))
            except ValueError:
                pass
    return max(nums) if nums else np.nan

def sanitize_column_name(col):
    col_str = str(col).strip()
    if "ttulo" in col_str.lower() or "titulo" in col_str.lower():
        return "Título da Revista"
    if "subrea" in col_str.lower() or "subarea" in col_str.lower():
        return "Subárea do Conhecimento"
    if "ndice h5" in col_str.lower() or "indice h5" in col_str.lower() or "ndice h5" in col_str.lower():
        return "Índice h5"
    if "grande area" in col_str.lower():
        return "Grande Area"
    if "area do" in col_str.lower():
        return "Area do Conhecimento"
    return col_str

def run_consolidation():
    if not os.path.exists(INPUT_FILE):
        print(f"Erro: Arquivo {INPUT_FILE} não encontrado.")
        return

    print(f"--- Carregando {INPUT_FILE} para consolidação ---")
    df = pd.read_excel(INPUT_FILE)
    
    # Sanitiza todos os nomes de colunas
    df.columns = [sanitize_column_name(col) for col in df.columns]
    print("Colunas sanitizadas com sucesso:", list(df.columns))

    n_rows = len(df)
    print(f"Total de linhas originais: {n_rows}")

    # Pré-processa chaves de agrupamento
    df['clean_issn'] = df['ISSN'].apply(clean_issn)
    df['clean_title'] = df['Título da Revista'].apply(clean_title)

    # DSU para agrupar componentes conexos
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

    # Mapeia cada índice de linha para o seu grupo representante
    df['group_root'] = [dsu.find(i) for i in range(n_rows)]
    
    grouped = df.groupby('group_root')
    print(f"Número de revistas únicas após consolidação: {grouped.ngroups}")

    consolidated_rows = []

    # Processa cada grupo aplicando as regras de mesclagem
    for root, group in grouped:
        row_data = {}
        
        # Título da Revista e ISSN
        row_data['Título da Revista'] = choose_best_title(group['Título da Revista'])
        row_data['ISSN'] = merge_issns(group['ISSN'])
        
        # Homepage
        row_data['Homepage'] = first_non_null(group['Homepage'])
        if pd.isna(row_data['Homepage']):
            row_data['Homepage'] = ""

        # Aims and Scope
        scopes = [str(s).strip() for s in group['Aims and Scope'] if pd.notna(s) and str(s).strip() not in ["", "-", "nan"]]
        row_data['Aims and Scope'] = max(scopes, key=len) if scopes else ""

        # Áreas de conhecimento (Deduplicadas e ordenadas)
        row_data['Grande Area'] = merge_categorical_field(group['Grande Area'])
        row_data['Area do Conhecimento'] = merge_categorical_field(group['Area do Conhecimento'])
        row_data['Subárea do Conhecimento'] = merge_categorical_field(group['Subárea do Conhecimento'])

        # Indexadores (Limitação estrita para Web of Science e Scopus)
        row_data['Indexador'] = merge_indexers(group['Indexador'])

        # Métricas científicas
        row_data['JIF'] = max_numeric(group['JIF'])
        row_data['Quartil JCR'] = merge_categorical_field(group['Quartil JCR'])
        row_data['SJR'] = max_numeric(group['SJR'])
        row_data['SJR Best Quartile'] = merge_categorical_field(group['SJR Best Quartile'])
        row_data['H index'] = max_numeric(group['H index'])
        row_data['Índice h5'] = max_numeric(group['Índice h5'])

        consolidated_rows.append(row_data)

    # Cria o DataFrame consolidado
    df_consolidated = pd.DataFrame(consolidated_rows)

    # Ordena pelo título
    df_consolidated['sort_key'] = df_consolidated['Título da Revista'].apply(clean_title)
    df_consolidated = df_consolidated.sort_values(by='sort_key').drop(columns=['sort_key'])

    # Adiciona a numeração sequencial 'N' (1.0, 2.0, 3.0...)
    df_consolidated.insert(0, 'N', [float(i + 1) for i in range(len(df_consolidated))])

    # Remove colunas extra/temporárias se existirem
    if 'Unnamed: 15' in df_consolidated.columns:
        df_consolidated = df_consolidated.drop(columns=['Unnamed: 15'])

    # Salva no arquivo consolidado
    df_consolidated.to_excel(OUTPUT_FILE, index=False)
    print(f"Salvo arquivo consolidado: {OUTPUT_FILE}")

    # Salva também sobrescrevendo o original
    df_consolidated.to_excel(INPUT_FILE, index=False)
    print(f"Sobrescrito arquivo original para atualização: {INPUT_FILE}")

if __name__ == "__main__":
    run_consolidation()

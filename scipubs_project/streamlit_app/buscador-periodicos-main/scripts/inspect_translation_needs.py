import pandas as pd

df = pd.read_csv('dados_complemento.csv', sep=';', encoding='utf-8-sig', low_memory=False)

col_src = "Aims and Scope"
col_dst = "Aims and Scope (translate)"

if col_dst not in df.columns:
    idx_src = df.columns.get_loc(col_src)
    df.insert(idx_src + 1, col_dst, "")

has_scope = df[col_src].notna() & (df[col_src].astype(str).str.strip() != "") & (df[col_src].astype(str).str.strip() != "-")
has_trans = df[col_dst].notna() & (df[col_dst].astype(str).str.strip() != "") & (df[col_dst].astype(str).str.strip() != "-")

print(f"Total de linhas em dados_complemento.csv: {len(df)}")
print(f"Linhas com Aims and Scope preenchido: {has_scope.sum()}")
print(f"Linhas ja traduzidas em Aims and Scope (translate): {has_trans.sum()}")
print(f"Linhas pendentes de traducao: {(has_scope & (~has_trans)).sum()}")

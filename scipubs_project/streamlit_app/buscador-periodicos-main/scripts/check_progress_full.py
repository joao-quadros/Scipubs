import pandas as pd

df = pd.read_csv('dados_2.csv', sep=';', encoding='utf-8-sig', low_memory=False)

col_aims = "Aims and Scope"
col_h5_idx = "Índice h5"
col_h5_med = "Mediana h5"

total = len(df)

has_aims = df[col_aims].notna() & (df[col_aims].astype(str).str.strip() != '') & (df[col_aims].astype(str).str.strip() != '-')
has_h5_idx = df[col_h5_idx].notna() & (df[col_h5_idx].astype(str).str.strip() != '') & (df[col_h5_idx].astype(str).str.strip() != '-')
has_h5_med = df[col_h5_med].notna() & (df[col_h5_med].astype(str).str.strip() != '') & (df[col_h5_med].astype(str).str.strip() != '-')

# Linhas totalmente preenchidas com ambas as informações
complete = has_aims & (has_h5_idx | has_h5_med)

# Linhas pendentes
pending_aims = (~has_aims).sum()
pending_h5 = (~(has_h5_idx | has_h5_med)).sum()
pending_total = ((~has_aims) | (~(has_h5_idx | has_h5_med))).sum()

print(f"Total de revistas na base: {total}")
print(f"Com Aims and Scope: {has_aims.sum()}")
print(f"Com Índice h5 / Mediana h5: {(has_h5_idx | has_h5_med).sum()}")
print(f"Totalmente completas: {complete.sum()}")
print(f"Faltam processar Aims & Scope: {pending_aims}")
print(f"Faltam processar Métricas h5: {pending_h5}")
print(f"Total de revistas ainda pendentes: {pending_total}")

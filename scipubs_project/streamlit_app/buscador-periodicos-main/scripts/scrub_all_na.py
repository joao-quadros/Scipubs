import pandas as pd
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

file_path = "dados_Antigravity.csv"
df = pd.read_csv(file_path, sep=';', encoding='utf-8-sig', low_memory=False)

col_scope = "Aims and Scope"
col_trans = "Aims and Scope (translate)"

if col_scope in df.columns:
    df[col_scope] = df[col_scope].astype("object").fillna("").astype(str)
    # Substitui qualquer texto contendo não encontrada / not found por string vazia ""
    mask_pt = df[col_scope].str.contains("não encontrada|not found|nao encontrada", case=False, na=False)
    df.loc[mask_pt, col_scope] = ""

if col_trans in df.columns:
    df[col_trans] = df[col_trans].astype("object").fillna("").astype(str)
    mask_en = df[col_trans].str.contains("not found|não encontrada|nao encontrada", case=False, na=False)
    df.loc[mask_en, col_trans] = ""

df.to_csv(file_path, sep=';', index=False, encoding='utf-8-sig')

# Verificação
cnt_pt = df[col_scope].str.contains("não encontrada|not found", case=False, na=False).sum()
cnt_en = df[col_trans].str.contains("not found|não encontrada", case=False, na=False).sum()

print("--- LIMPEZA TOTAL CONCLUÍDA ---")
print(f"Restantes 'não encontrada' na Coluna D: {cnt_pt}")
print(f"Restantes 'not found' na Coluna E: {cnt_en}")

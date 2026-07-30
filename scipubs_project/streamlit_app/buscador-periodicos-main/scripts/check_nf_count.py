import pandas as pd
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

df = pd.read_csv('dados_Antigravity.csv', sep=';', encoding='utf-8-sig', low_memory=False)
col_scope = "Aims and Scope"

nf_mask = df[col_scope].astype(str).str.contains('não encontrada|not found', case=False, na=False)
empty_mask = df[col_scope].isna() | (df[col_scope].astype(str).str.strip() == '') | (df[col_scope].astype(str).str.strip() == '-')

print(f"dados_Antigravity.csv Total: {len(df)}")
print(f"dados_Antigravity.csv 'Informação não encontrada': {nf_mask.sum()}")
print(f"dados_Antigravity.csv Vazios: {empty_mask.sum()}")

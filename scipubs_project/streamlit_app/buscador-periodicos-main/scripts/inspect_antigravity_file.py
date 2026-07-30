import pandas as pd
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

df = pd.read_csv('dados_Antigravity.csv', sep=';', encoding='utf-8-sig', low_memory=False)

col_title = df.columns[0]
col_issn = df.columns[1]
col_hp = df.columns[2]
col_scope = "Aims and Scope"
col_trans = "Aims and Scope (translate)"

has_scope = df[col_scope].notna() & (df[col_scope].astype(str).str.strip() != "") & (df[col_scope].astype(str).str.strip() != "-")
has_trans = df[col_trans].notna() & (df[col_trans].astype(str).str.strip() != "") & (df[col_trans].astype(str).str.strip() != "-")

print(f"Total de linhas em dados_Antigravity.csv: {len(df)}")
print(f"Linhas com Aims and Scope preenchido: {has_scope.sum()}")
print(f"Linhas com Aims and Scope (translate) preenchido: {has_trans.sum()}")
print(f"Linhas pendentes de processamento: {(~has_scope).sum()}")

print("\n--- AMOSTRA DAS PRIMEIRAS 5 REVISTAS ---")
for idx, r in df.head(5).iterrows():
    print(f"\n🔹 Rev #{idx+1}: {r[col_title]} (ISSN: {r[col_issn]})")
    print(f"   URL: {r[col_hp]}")
    print(f"   Aims & Scope atual: {str(r[col_scope])[:100]}...")

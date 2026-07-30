import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import pandas as pd

df = pd.read_csv('dados_new_atualizado.csv', sep=';', encoding='utf-8-sig', low_memory=False)
col_title = df.columns[0]
col_issn = df.columns[1]
col_hp = df.columns[2]
col_scope = "Aims and Scope"

print(f"Total de linhas em dados_new_atualizado.csv: {len(df)}")
filled = df[df[col_scope].notna() & (df[col_scope].astype(str).str.strip() != "") & (df[col_scope].astype(str).str.strip() != "-")]
print(f"Linhas com perfil editorial preenchido: {len(filled)}")

print("\n--- EXEMPLOS DOS PRIMEIROS PERIÓDICOS PROCESSADOS ---")
for idx, r in filled.head(5).iterrows():
    title = r[col_title]
    issn = r[col_issn]
    hp = r[col_hp]
    scope_val = str(r[col_scope])
    
    print(f"\n🔹 Rev #{idx+1}: {title} (ISSN: {issn})")
    print(f"   URL: {hp}")
    print(f"   Perfil Editorial: {scope_val[:350]}...")

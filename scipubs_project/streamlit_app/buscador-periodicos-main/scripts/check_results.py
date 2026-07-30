import pandas as pd
df = pd.read_csv('dados_2.csv', sep=';', encoding='utf-8-sig', low_memory=False)
col_title = df.columns[0]
filled = df[df['Aims and Scope'].notna() & (df['Aims and Scope'].astype(str).str.strip() != '')]
print(f"Total de revistas com Aims and Scope preenchido: {len(filled)}")
print("\nExemplos de Aims & Scope extraidos:")
for idx, r in filled.head(5).iterrows():
    title = r[col_title]
    issn = r.get('ISSN', '-')
    scope = str(r['Aims and Scope'])
    print(f"=== {title} (ISSN: {issn}) ===")
    print(scope[:300] + "\n")

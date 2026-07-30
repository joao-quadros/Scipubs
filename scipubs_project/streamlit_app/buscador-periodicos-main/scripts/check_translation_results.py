import pandas as pd

df = pd.read_csv('dados_complemento.csv', sep=';', encoding='utf-8-sig', low_memory=False)
col_title = df.columns[0]
col_src = "Aims and Scope"
col_dst = "Aims and Scope (translate)"

filled_dst = df[df[col_dst].notna() & (df[col_dst].astype(str).str.strip() != '') & (df[col_dst].astype(str).str.strip() != '-')]

print(f"Total de revistas com Aims and Scope (translate) preenchido: {len(filled_dst)}")
print("\nExemplos de Tradução (Original vs Inglês Acadêmico):")

for idx, r in filled_dst.head(5).iterrows():
    title = r[col_title]
    src = str(r[col_src])[:120]
    dst = str(r[col_dst])[:120]
    print(f"=== Linha {idx+2}: {title} ===")
    print(f"Original : {src}...")
    print(f"Traduzido: {dst}...\n")

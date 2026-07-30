import pandas as pd

df = pd.read_csv('dados_2.csv', sep=';', encoding='utf-8-sig', low_memory=False)
col_aims = 'Aims and Scope'
col_title = df.columns[0]

filled_df = df[df[col_aims].notna() & (df[col_aims].astype(str).str.strip() != '') & (df[col_aims].astype(str).str.strip() != '-')]

print(f"Total de linhas preenchidas ate agora: {len(filled_df)}")
print("\nPrimeiras 10 linhas preenchidas (numero da linha no Excel):")

for idx, r in filled_df.head(10).iterrows():
    excel_row = idx + 2  # Linha 1 e o cabecalho
    title = str(r[col_title])
    scope = str(r[col_aims])[:80]
    print(f"Linha {excel_row}: [{title}] -> {scope}...")

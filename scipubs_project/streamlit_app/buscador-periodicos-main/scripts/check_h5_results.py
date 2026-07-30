import pandas as pd

df = pd.read_csv('dados_2.csv', sep=';', encoding='utf-8-sig', low_memory=False)
col_title = df.columns[0]

filled_h5 = df[df['Mediana h5'].notna() & (df['Mediana h5'].astype(str).str.strip() != '') & (df['Mediana h5'].astype(str).str.strip() != '-')]

print(f"Total de revistas com Mediana h5 preenchido: {len(filled_h5)}")
print("\nExemplos de Revistas com Índice h5 e Mediana h5 extraídos:")
for idx, r in filled_h5.head(10).iterrows():
    title = r[col_title]
    h5_idx = r.get('Índice h5', '-')
    h5_med = r.get('Mediana h5', '-')
    print(f"Linha {idx+2} (Excel): {title} | Índice h5: {h5_idx} | Mediana h5: {h5_med}")

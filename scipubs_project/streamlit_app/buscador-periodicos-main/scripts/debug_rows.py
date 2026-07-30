import pandas as pd
df = pd.read_csv('dados_2.csv', sep=';', encoding='utf-8-sig', low_memory=False)
col_title = df.columns[0]
for idx in range(20):
    row = df.iloc[idx]
    print(f"Row {idx}: Title={row[col_title]} | ISSN={row.get('ISSN')} | HP={row.get('Homepage')}")

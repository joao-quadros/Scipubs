import pandas as pd

df = pd.read_csv('dados_complemento.csv', sep=';', encoding='utf-8-sig', nrows=5)
print("Colunas:", list(df.columns))

df_full = pd.read_csv('dados_complemento.csv', sep=';', encoding='utf-8-sig', low_memory=False)
print("Total de linhas:", len(df_full))

# Verifica Coluna E (index 4) ou por nome
for idx, col in enumerate(df_full.columns):
    print(f"Coluna {idx} ({chr(65+idx)}): {col}")

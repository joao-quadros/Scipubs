import pandas as pd
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

df_ant = pd.read_csv("dados_Antigravity.csv", sep=';', encoding='utf-8-sig', on_bad_lines='skip', low_memory=False)
df_d2 = pd.read_csv("dados_2.csv", sep=';', encoding='utf-8-sig', on_bad_lines='skip', low_memory=False)

print("--- DEPURANDO COLUNAS E VALORES ---")
print("dados_Antigravity.csv colunas:", list(df_ant.columns))
print("dados_2.csv colunas:", list(df_d2.columns))

print("\nAmostra dados_Antigravity.csv (Primeiras 5 linhas):")
print(df_ant.iloc[:5, :3])

print("\nAmostra dados_2.csv (Primeiras 5 linhas):")
print(df_d2.iloc[:5, :5])

c_scope2 = df_d2.columns[3]
valid_d2 = df_d2[df_d2[c_scope2].fillna('').astype(str).str.len() > 25]
print(f"\nTotal de linhas com escopo em dados_2.csv: {len(valid_d2)}")

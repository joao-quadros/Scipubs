import pandas as pd
import csv
import sys
import os

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

print("=== DEPURANDO E RESTAURANDO DADOS_ANTIGRAVITY.CSV COM QUOTING SEGURO ===")

# Recarrega o arquivo original limpo de dados_complemento.csv / dados_2.csv ou backup
src_file = "dados_complemento.csv" if os.path.exists("dados_complemento.csv") else "dados_2.csv"
target_file = "dados_Antigravity.csv"

# Carrega o mapa de escopos salvando em memória com segurança
scope_map = {}

# 1. Carrega escopos pré-existentes de dados_2.csv
if os.path.exists("dados_2.csv"):
    try:
        df_d2 = pd.read_csv("dados_2.csv", sep=';', encoding='utf-8-sig', on_bad_lines='skip', low_memory=False)
        c_title = df_d2.columns[0]
        c_issn = df_d2.columns[1]
        c_sc = df_d2.columns[3]
        c_tr = df_d2.columns[4]

        for _, r in df_d2.iterrows():
            title = str(r.get(c_title, "")).strip().lower()
            issn = str(r.get(c_issn, "")).strip().lower().replace("-", "")
            scope = str(r.get(c_sc, "")).strip()
            trans = str(r.get(c_tr, "")).strip()

            if len(scope) > 25 and "não encontrada" not in scope.lower() and "not found" not in scope.lower():
                # Remove ponto e vírgula interno para não quebrar CSV
                scope_clean = scope.replace(";", ",")
                trans_clean = trans.replace(";", ",")
                if issn and issn not in ["-", "", "nan", "none"]:
                    scope_map[("issn", issn)] = (scope_clean, trans_clean)
                if title and title not in ["-", "", "nan", "none"]:
                    scope_map[("title", title)] = (scope_clean, trans_clean)
    except Exception as e:
        print(f"Erro em dados_2.csv: {e}")

print(f"Total de Escopos Validados no Mapa de Conhecimento: {len(scope_map)}")

# 2. Carrega as 27.274 revistas do arquivo fonte principal
df_main = pd.read_csv(src_file, sep=';', encoding='utf-8-sig', on_bad_lines='skip', low_memory=False)

col_title = df_main.columns[0]
col_issn = df_main.columns[1]
col_scope = "Aims and Scope"
col_trans = "Aims and Scope (translate)"

if col_scope not in df_main.columns:
    df_main.insert(3, col_scope, "")
if col_trans not in df_main.columns:
    df_main.insert(4, col_trans, "")

df_main[col_scope] = df_main[col_scope].astype("object").fillna("").astype(str)
df_main[col_trans] = df_main[col_trans].astype("object").fillna("").astype(str)

# Preenche os escopos válidos salvos do mapa de conhecimento
matches = 0
for idx, r in df_main.iterrows():
    title = str(r.get(col_title, "")).strip().lower()
    issn = str(r.get(col_issn, "")).strip().lower().replace("-", "")

    found = None
    if ("issn", issn) in scope_map:
        found = scope_map[("issn", issn)]
    elif ("title", title) in scope_map:
        found = scope_map[("title", title)]

    if found:
        df_main.loc[idx, col_scope] = found[0]
        df_main.loc[idx, col_trans] = found[1]
        matches += 1

# Garante limpeza completa de qualquer menção de 'não encontrada'
mask_clean1 = df_main[col_scope].str.contains("não encontrada|not found", case=False, na=False)
df_main.loc[mask_clean1, col_scope] = ""
mask_clean2 = df_main[col_trans].str.contains("not found|não encontrada", case=False, na=False)
df_main.loc[mask_clean2, col_trans] = ""

# Salva dados_Antigravity.csv com quoting seguro QUOTE_ALL para evitar corrupção por ponto e vírgula
df_main.to_csv(target_file, sep=';', index=False, encoding='utf-8-sig', quoting=csv.QUOTE_ALL)

print(f"\n✅ RECONSTRUÇÃO COMPLETA DE {target_file}:")
print(f"   Total de Linhas no Arquivo: {len(df_main)}")
print(f"   Revistas com Escopo Válido Preenchido: {matches} ({(matches/len(df_main))*100:.1f}%)")
print(f"   Lacunas Vazias Pendentes: {len(df_main) - matches}")

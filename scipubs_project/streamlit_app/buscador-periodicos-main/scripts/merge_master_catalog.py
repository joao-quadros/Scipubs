import pandas as pd
import sys
import os

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

print("=== REVISÃO E UNIFICAÇÃO MASTER DE ESCOPOS PRÉ-MINERADOS EM DADOS_ANTIGRAVITY.CSV ===")

path_target = "dados_Antigravity.csv"
if not os.path.exists(path_target):
    print(f"Erro: {path_target} não encontrado.")
    sys.exit(1)

df_target = pd.read_csv(path_target, sep=';', encoding='utf-8-sig', low_memory=False)

col_title = df_target.columns[0]
col_issn = df_target.columns[1]
col_scope = "Aims and Scope"
col_trans = "Aims and Scope (translate)"

if col_scope not in df_target.columns:
    df_target.insert(3, col_scope, "")
if col_trans not in df_target.columns:
    df_target.insert(4, col_trans, "")

df_target[col_scope] = df_target[col_scope].astype("object").fillna("").astype(str)
df_target[col_trans] = df_target[col_trans].astype("object").fillna("").astype(str)

# Limpa textos "não encontrada"
mask_pt = df_target[col_scope].str.contains("não encontrada|not found", case=False, na=False)
df_target.loc[mask_pt, col_scope] = ""
mask_en = df_target[col_trans].str.contains("not found|não encontrada", case=False, na=False)
df_target.loc[mask_en, col_trans] = ""

# Constrói o Mapa Mestre de Conhecimento a partir de dados_2.csv, dados_new_atualizado.csv e outros backups
knowledge_map = {}

source_files = ["dados_2.csv", "dados_new_atualizado.csv", "dados_parcial.csv"]

for sf in source_files:
    if os.path.exists(sf):
        try:
            df_src = pd.read_csv(sf, sep=';', encoding='utf-8-sig', low_memory=False)
            c_title = df_src.columns[0]
            c_issn = df_src.columns[1]
            c_sc = "Aims and Scope" if "Aims and Scope" in df_src.columns else df_src.columns[3]
            c_tr = "Aims and Scope (translate)" if "Aims and Scope (translate)" in df_src.columns else df_src.columns[4]

            for _, r in df_src.iterrows():
                stitle = str(r.get(c_title, "")).strip().lower()
                sissn = str(r.get(c_issn, "")).strip().lower().replace("-", "")
                sscope = str(r.get(c_sc, "")).strip()
                strans = str(r.get(c_tr, "")).strip()

                if len(sscope) > 25 and "não encontrada" not in sscope.lower() and "not found" not in sscope.lower():
                    if sissn and sissn not in ["-", "", "nan", "none"]:
                        knowledge_map[("issn", sissn)] = (sscope, strans)
                    if stitle and stitle not in ["-", "", "nan", "none"]:
                        knowledge_map[("title", stitle)] = (sscope, strans)
        except Exception as e:
            print(f"Aviso ao ler {sf}: {e}")

print(f"Total de Perfis Editoriais Únicos no Catálogo Mestre: {len(knowledge_map)}")

# Aplica o mapeamento completo sobre dados_Antigravity.csv
recovered_count = 0
for idx, r in df_target.iterrows():
    cur_scope = str(r.get(col_scope, "")).strip()
    if len(cur_scope) <= 25:
        title = str(r.get(col_title, "")).strip().lower()
        issn = str(r.get(col_issn, "")).strip().lower().replace("-", "")

        matched = None
        if ("issn", issn) in knowledge_map:
            matched = knowledge_map[("issn", issn)]
        elif ("title", title) in knowledge_map:
            matched = knowledge_map[("title", title)]

        if matched:
            df_target.loc[idx, col_scope] = matched[0]
            df_target.loc[idx, col_trans] = matched[1]
            recovered_count += 1

df_target.to_csv(path_target, sep=';', index=False, encoding='utf-8-sig')

# Auditoria pós-fusão
s_final = df_target[col_scope].fillna('').astype(str).str.strip()
valid_final = (s_final.str.len() > 25) & (~s_final.str.contains('não encontrada|not found', case=False))

print(f"\n✅ AUDITORIA CONCLUÍDA:")
print(f"   Novos Escopos Restaurados dos Arquivos Anteriores: {recovered_count}")
print(f"   TOTAL DE ESCOPOS VÁLIDOS EM DADOS_ANTIGRAVITY.CSV: {valid_final.sum()} de {len(df_target)} ({(valid_final.sum()/len(df_target))*100:.1f}%)")
print(f"   Lacunas Vazias Pendentes: {len(df_target) - valid_final.sum()}")

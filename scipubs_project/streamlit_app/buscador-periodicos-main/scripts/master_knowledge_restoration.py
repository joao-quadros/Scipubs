import pandas as pd
import requests
import urllib.parse
import re
import os
import sys
import csv

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

print("=== INICIANDO RESTAURAÇÃO COMPLETA DO MAPA MESTRE DE ESCOPOS DA BASE DE DADOS ===")

def translate_to_academic_english(text):
    if not text or str(text).strip() in ["-", "", "nan", "None", "Informação não encontrada"]:
        return ""
    text_clean = re.sub(r'\s+', ' ', str(text)).strip()
    if len(text_clean) < 10:
        return text_clean
    text_low = text_clean.lower()
    if sum(1 for w in ["the ", " journal", "publishes ", "peer-reviewed", "research"] if w in text_low) >= 2:
        return text_clean
    try:
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=en&dt=t&q={urllib.parse.quote(text_clean[:2000])}"
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            sentences = r.json()[0]
            trans = "".join([s[0] for s in sentences if s and len(s) > 0 and s[0]])
            if trans and len(trans.strip()) > 5:
                return re.sub(r'\s+', ' ', trans).strip()
    except Exception:
        pass
    return text_clean

master_map = {}

def load_file_scopes(filepath):
    if not os.path.exists(filepath):
        return
    print(f"Lendo {filepath}...")
    df = None
    for sep in [';', ',']:
        for enc in ['utf-8-sig', 'latin1', 'cp1252']:
            try:
                df_temp = pd.read_csv(filepath, sep=sep, encoding=enc, on_bad_lines='skip', low_memory=False)
                if len(df_temp.columns) >= 4:
                    df = df_temp
                    break
            except Exception:
                pass
        if df is not None:
            break

    if df is None or len(df.columns) < 4:
        print(f"Ignorando {filepath} (estrutura incompatível).")
        return

    col_t = df.columns[0]
    col_i = df.columns[1]
    col_sc = "Aims and Scope" if "Aims and Scope" in df.columns else df.columns[3]
    col_tr = "Aims and Scope (translate)" if "Aims and Scope (translate)" in df.columns else None

    count = 0
    for _, r in df.iterrows():
        title = str(r.get(col_t, "")).strip().lower()
        issn = str(r.get(col_i, "")).strip().lower().replace("-", "")
        scope = str(r.get(col_sc, "")).strip()
        trans = str(r.get(col_tr, "")).strip() if col_tr and col_tr in r else ""

        if len(scope) > 20 and "não encontrada" not in scope.lower() and "not found" not in scope.lower():
            scope_clean = scope.replace(";", ",")
            trans_clean = trans.replace(";", ",") if trans else ""
            
            entry = (scope_clean, trans_clean)
            if issn and issn not in ["-", "", "nan", "none"]:
                master_map[("issn", issn)] = entry
            if title and title not in ["-", "", "nan", "none"]:
                master_map[("title", title)] = entry
            count += 1
    print(f"   -> {count} escopos carregados de {filepath}")

for fn in ["dados_2.csv", "dados_new_atualizado.csv", "dados_complemento.csv"]:
    load_file_scopes(fn)

print(f"Total de Perfis Editoriais Únicos Catalogados no Mapa Mestre: {len(master_map)}")

# Carrega dados_Antigravity.csv
target_file = "dados_Antigravity.csv"
df_target = None
for enc in ['utf-8-sig', 'latin1', 'cp1252']:
    try:
        df_target = pd.read_csv(target_file, sep=';', encoding=enc, on_bad_lines='skip', low_memory=False)
        if len(df_target.columns) >= 3:
            break
    except Exception:
        pass

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

recovered = 0

for idx, r in df_target.iterrows():
    cur_sc = str(r.get(col_scope, "")).strip()
    if len(cur_sc) <= 20:
        title = str(r.get(col_title, "")).strip().lower()
        issn = str(r.get(col_issn, "")).strip().lower().replace("-", "")

        found = None
        if ("issn", issn) in master_map:
            found = master_map[("issn", issn)]
        elif ("title", title) in master_map:
            found = master_map[("title", title)]

        if found:
            sc_val, tr_val = found
            df_target.loc[idx, col_scope] = sc_val
            if not tr_val or len(tr_val) < 10:
                tr_val = translate_to_academic_english(sc_val)
            df_target.loc[idx, col_trans] = tr_val
            recovered += 1

# Garante limpeza total de 'não encontrada'
mask_c1 = df_target[col_scope].str.contains("não encontrada|not found", case=False, na=False)
df_target.loc[mask_c1, col_scope] = ""
mask_c2 = df_target[col_trans].str.contains("not found|não encontrada", case=False, na=False)
df_target.loc[mask_c2, col_trans] = ""

df_target.to_csv(target_file, sep=';', index=False, encoding='utf-8-sig', quoting=csv.QUOTE_ALL)

s_final = df_target[col_scope].fillna('').astype(str).str.strip()
valid_final = (s_final.str.len() > 20) & (~s_final.str.contains('não encontrada|not found', case=False))

print(f"\n🎉 RESTAURAÇÃO MASTER CONCLUÍDA COM SUCESSO!")
print(f"   Total de Linhas no dados_Antigravity.csv: {len(df_target)}")
print(f"   🟢 TOTAL DE ESCOPOS VÁLIDOS RESTAURADOS E PREENCHIDOS: {valid_final.sum()} de {len(df_target)} ({(valid_final.sum()/len(df_target))*100:.1f}%)")
print(f"   ⚪ Lacunas Vazias Pendentes: {len(df_target) - valid_final.sum()}")

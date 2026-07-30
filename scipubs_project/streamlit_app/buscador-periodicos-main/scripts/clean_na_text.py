import pandas as pd
import sys
import os

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

file_path = "dados_Antigravity.csv"
if os.path.exists(file_path):
    print(f"--- Substituindo mensagens 'Informação não encontrada' por lacunas vazias em {file_path} ---")
    df = pd.read_csv(file_path, sep=';', encoding='utf-8-sig', low_memory=False)
    
    col_scope = "Aims and Scope"
    col_trans = "Aims and Scope (translate)"
    
    if col_scope in df.columns:
        df[col_scope] = df[col_scope].astype("object").fillna("").astype(str)
        # Substitui variações de 'informação não encontrada' por lacuna vazia ''
        mask_pt = df[col_scope].str.contains("Informação não encontrada|informação não encontrada|Informao no encontrada", case=False, na=False)
        count_pt = mask_pt.sum()
        df.loc[mask_pt, col_scope] = ""
        print(f"[OK] Coluna D ({col_scope}): {count_pt} mensagens substituídas por lacunas vazias!")

    if col_trans in df.columns:
        df[col_trans] = df[col_trans].astype("object").fillna("").astype(str)
        mask_en = df[col_trans].str.contains("Information not found|information not found", case=False, na=False)
        count_en = mask_en.sum()
        df.loc[mask_en, col_trans] = ""
        print(f"[OK] Coluna E ({col_trans}): {count_en} mensagens substituídas por lacunas vazias!")

    df.to_csv(file_path, sep=';', index=False, encoding='utf-8-sig')
    print("--- Substituição concluída com sucesso! ---")
else:
    print(f"Arquivo {file_path} não encontrado.")

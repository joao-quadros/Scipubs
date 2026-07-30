import sys
sys.path.append('.')
import pandas as pd
from scripts.translate_aims_scope import translate_to_academic_english

df = pd.read_csv('dados_complemento.csv', sep=';', encoding='utf-8-sig', low_memory=False)
col_src = "Aims and Scope"
col_title = df.columns[0]

count = 0
for idx, r in df.iterrows():
    txt = str(r[col_src])
    if any(pt in txt.lower() for pt in ["publica", "revista", "escopo", "missao", "objetivo"]):
        print(f"=== Linha {idx+2}: {r[col_title]} ===")
        print("Original :", txt[:180])
        print("Traduzido:", translate_to_academic_english(txt)[:180])
        print()
        count += 1
        if count >= 3:
            break

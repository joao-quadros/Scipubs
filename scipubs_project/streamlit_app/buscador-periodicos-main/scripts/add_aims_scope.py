import pandas as pd
import os

files = ['dados.csv', 'dados_revistas.csv']

for fn in files:
    if not os.path.exists(fn):
        print(f"Arquivo {fn} não encontrado. Pulando.")
        continue
        
    print(f"Processando {fn}...")
    try:
        # Detecta separador e lê
        df = pd.read_csv(fn, sep=';', encoding='utf-8-sig', low_memory=False)
        
        # Corrige possíveis nomes de colunas com problemas de encoding
        rename_dict = {}
        for col in df.columns:
            if 'Grande' in col and 'Area' in col:
                rename_dict[col] = 'Grande Area'
            if 'Sub' in col and 'area' in col.lower():
                rename_dict[col] = 'Subárea do Conhecimento'
            if 'Area do Conhecimento' in col or 'rea do Conhecimento' in col:
                rename_dict[col] = 'Area do Conhecimento'
                
        if rename_dict:
            df = df.rename(columns=rename_dict)
            
        if 'Aims e Escopo' not in df.columns:
            # Cria a coluna concatenando as áreas
            df['Aims e Escopo'] = df.apply(
                lambda r: f"{str(r.get('Grande Area','')).strip()} - {str(r.get('Area do Conhecimento','')).strip()} - {str(r.get('Subárea do Conhecimento','')).strip()}".replace('nan', '').strip(' -'),
                axis=1
            )
            # Salva de volta
            df.to_csv(fn, sep=';', index=False, encoding='utf-8-sig')
            print(f"Sucesso: Coluna 'Aims e Escopo' adicionada a {fn}.")
        else:
            print(f"A coluna 'Aims e Escopo' já existe em {fn}.")
            
    except Exception as e:
        print(f"Erro ao processar {fn}: {e}")

print("Concluído!")

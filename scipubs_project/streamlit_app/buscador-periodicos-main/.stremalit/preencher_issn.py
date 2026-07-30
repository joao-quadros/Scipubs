import pandas as pd
import sys
import os

def preencher_issn(input_file):
    if not os.path.exists(input_file):
        print(f"Erro: O arquivo '{input_file}' não foi encontrado.")
        return

    print(f"Lendo o arquivo: {input_file}...")
    try:
        df = pd.read_csv(input_file)
    except Exception as e:
        print(f"Erro ao ler o arquivo: {e}")
        return

    if 'ISSN' not in df.columns or 'ISSN-e' not in df.columns:
        print("Erro: As colunas 'ISSN' e 'ISSN-e' precisam existir no arquivo.")
        return

    # Trata espaços em branco como nulos e preenche com o valor de ISSN
    df['ISSN-e'] = df['ISSN-e'].replace(r'^\s*$', float('NaN'), regex=True).fillna(df['ISSN'])

    nome, ext = os.path.splitext(input_file)
    output_file = f"{nome}_atualizado{ext}"

    try:
        df.to_csv(output_file, index=False)
        print(f"Sucesso! Arquivo modificado salvo em: {output_file}")
    except Exception as e:
        print(f"Erro ao salvar o arquivo: {e}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python preencher_issn.py <nome_do_arquivo.csv>")
    else:
        preencher_issn(sys.argv[1])
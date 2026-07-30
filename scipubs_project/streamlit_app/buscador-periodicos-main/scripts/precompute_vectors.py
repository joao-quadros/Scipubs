"""
Script para pré-computar embeddings do catálogo de revistas.
Deve ser executado localmente antes do deploy no Streamlit Cloud.
"""

import os
import sys
import pickle
import numpy as np
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.embeddings_client import EmbeddingsClient


def carregar_dados():
    nome = "dados.csv"
    if not os.path.exists(nome):
        if os.path.exists("Dados.csv"):
            nome = "Dados.csv"
        elif os.path.exists("DADOS.CSV"):
            nome = "DADOS.CSV"

    with open(nome, "r", encoding="utf-8-sig", errors="ignore") as f:
        linha = f.readline()
    sep = ";" if linha.count(";") >= linha.count(",") else ","

    df = pd.read_csv(nome, sep=sep, encoding="utf-8-sig", low_memory=False, on_bad_lines="skip")
    df.columns = df.columns.str.replace("\ufeff", "", regex=False)
    df.columns = [c.strip() for c in df.columns]
    df.columns = [c.replace("Grande Area", "Grande Área")
                    .replace("Area do Conhecimento", "Área do Conhecimento")
                    .replace("Subarea do Conhecimento", "Subárea do Conhecimento")
                  for c in df.columns]
    return df


def build_catalog_texts(df):
    col_titulo = df.columns[0]
    texts = []
    for _, row in df.iterrows():
        partes = [str(row[col_titulo])]
        for col in ["Grande Área", "Área do Conhecimento", "Subárea do Conhecimento", "Indexador"]:
            if col in row.index:
                val = str(row[col])
                if val and val not in ["-", "nan", "None", ""]:
                    partes.append(val)
        texts.append(" ".join(partes))
    return texts


def main():
    print("Carregando dados...")
    df = carregar_dados()
    print(f"Revistas: {len(df)}")

    print("Construindo textos...")
    texts = build_catalog_texts(df)

    print("Pré-computando embeddings TF-IDF...")
    client = EmbeddingsClient(model="nomic-embed-text", fallback_dim=512)
    client.fit_tfidf(texts)
    vectors = client.embed_batch(texts)

    # Converte para float16 para reduzir tamanho do arquivo
    vectors_array = np.array(vectors, dtype=np.float16)

    os.makedirs("data", exist_ok=True)
    cache_path = "data/journal_vectors.pkl"
    with open(cache_path, "wb") as f:
        pickle.dump({
            "vectors": vectors_array,
            "texts": texts,
            "vocab": client._vocab,
            "idf": client._idf
        }, f)

    print(f"Embeddings salvos em {cache_path}")
    print(f"Vocabulário: {len(client._vocab)} termos")
    print(f"Tamanho: {os.path.getsize(cache_path) / (1024*1024):.1f} MB")


if __name__ == "__main__":
    main()

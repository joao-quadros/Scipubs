import os
import sys
import pandas as pd
import numpy as np
import pickle
import time

# Adiciona o diretório raiz ao path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import carregar_dados
from services.discovery_recommender import DiscoveryRecommender

print("Iniciando geração de embeddings...")
t0 = time.time()

# 1. Carrega dados.csv
nome_arquivo = "dados.csv"
if os.path.exists(nome_arquivo):
    mtime = os.path.getmtime(nome_arquivo)
    size = os.path.getsize(nome_arquivo)
else:
    mtime = 0.0
    size = 0.0

df_original, arquivo_usado = carregar_dados(mtime, size)
print(f"Base de dados carregada: {len(df_original)} linhas.")

# 2. Inicializa o Recommender para normalizar colunas
recommender = DiscoveryRecommender(df_local=df_original)
df_scoped = recommender.df_scoped

# 3. Prepara o corpus de escopos
col_scope = "Aims e Escopo" if "Aims e Escopo" in df_scoped.columns else "title"
scopes = df_scoped[col_scope].astype(str).tolist()
titles = df_scoped["title"].astype(str).tolist()

corpus = []
for t, s in zip(titles, scopes):
    scope_clean = s.strip()
    if not scope_clean or scope_clean.lower() in ["nan", "none", ""]:
        corpus.append(t)
    else:
        corpus.append(scope_clean)

print("Importando SentenceTransformer...")
from sentence_transformers import SentenceTransformer

print("Carregando modelo all-MiniLM-L6-v2...")
model = SentenceTransformer("all-MiniLM-L6-v2")

print(f"Codificando {len(corpus)} escopos. Isso pode levar de 1 a 2 minutos...")
embeddings = model.encode(corpus, show_progress_bar=True, batch_size=64)

# 4. Salva no formato pickle
output_path = "data/journal_vectors_sentence.pkl"
os.makedirs("data", exist_ok=True)
with open(output_path, "wb") as f:
    pickle.dump({
        "embeddings": embeddings,
        "model_name": "all-MiniLM-L6-v2",
        "length": len(corpus)
    }, f)

print(f"Embeddings salvos com sucesso em {output_path} em {time.time() - t0:.2f} segundos!")

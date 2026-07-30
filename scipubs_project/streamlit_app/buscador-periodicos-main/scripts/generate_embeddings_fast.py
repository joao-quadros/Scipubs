import os
import pandas as pd
import numpy as np
import pickle
import time

print("Iniciando geração super rápida de embeddings com fastembed (leitura direta)...")
t0 = time.time()

# 1. Carrega dados.csv diretamente via pandas para evitar contexto do Streamlit
nome_arquivo = "dados.csv"
if not os.path.exists(nome_arquivo):
    if os.path.exists("Dados.csv"):
        nome_arquivo = "Dados.csv"
    elif os.path.exists("DADOS.CSV"):
        nome_arquivo = "DADOS.CSV"

if not os.path.exists(nome_arquivo):
    print("Erro: dados.csv não encontrado!")
    sys.exit(1)

# Lê o CSV
df = pd.read_csv(nome_arquivo, sep=None, engine='python', encoding='utf-8')
print(f"Base de dados carregada diretamente: {len(df)} linhas.")

# 2. Normaliza colunas simplificado
# Encontra a coluna do escopo
col_scope = None
for col in df.columns:
    if any(x in str(col).lower() for x in ["aims and scope", "aims e escopo", "escopo", "aims & scope"]):
        col_scope = col
        break

# Encontra a coluna do título
col_title = None
for col in df.columns:
    if any(x in str(col).lower() for x in ["titulo da revista", "título da revista", "title"]):
        col_title = col
        break

if not col_title:
    col_title = df.columns[1] if len(df.columns) > 1 else df.columns[0]
if not col_scope:
    col_scope = col_title

print(f"Usando coluna de título: {col_title}")
print(f"Usando coluna de escopo: {col_scope}")

scopes = [str(x) for x in df[col_scope].tolist()]
titles = [str(x) for x in df[col_title].tolist()]

corpus = []
for t, s in zip(titles, scopes):
    scope_clean = s.strip()
    if not scope_clean or scope_clean.lower() in ["nan", "none", "", "n/a", "-"]:
        corpus.append(str(t))
    else:
        corpus.append(scope_clean)

print("Importando fastembed.TextEmbedding...")
from fastembed import TextEmbedding

print("Inicializando modelo de embedding...")
model = TextEmbedding()

print(f"Codificando {len(corpus)} escopos...")
t_encode_start = time.time()
embeddings_gen = model.embed(corpus)
embeddings = np.array(list(embeddings_gen))
print(f"Codificação concluída em {time.time() - t_encode_start:.2f} segundos!")

# 3. Salva no formato pickle
output_path = "data/journal_vectors_sentence.pkl"
os.makedirs("data", exist_ok=True)
with open(output_path, "wb") as f:
    pickle.dump({
        "embeddings": embeddings,
        "model_name": "fastembed/bge-small-en-v1.5",
        "length": len(corpus)
    }, f)

print(f"Embeddings salvos com sucesso em {output_path} em {time.time() - t0:.2f} segundos total!")

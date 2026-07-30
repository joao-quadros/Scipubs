import os
import sys

sys.path.append(r"C:\Users\jquad\Documents\app-revista")
from recomendar_regras import carregar_e_normalizar_base, obter_modelo_embeddings, precomputar_e_salvar_embeddings

CACHE_PATH = r"C:\Users\jquad\Documents\app-revista\data\aims_scope_minilm_vectors.pkl"

if os.path.exists(CACHE_PATH):
    print("Removendo cache antigo de embeddings...")
    os.remove(CACHE_PATH)
    
df = carregar_e_normalizar_base()
model = obter_modelo_embeddings()
precomputar_e_salvar_embeddings(df, model)
print("Recriação de embeddings concluída!")

"""
Atualiza embeddings no banco usando a API gratuita do Hugging Face Inference.
Evita carregar modelo localmente (que estava travando no Windows).
"""

import os
import sys
import time
import requests
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db_client import get_db_client

MODEL = "sentence-transformers/paraphrase-MiniLM-L3-v2"
API_URL = f"https://api-inference.huggingface.co/models/{MODEL}"
HEADERS = {"Authorization": f"Bearer {os.getenv('HF_TOKEN', '')}"} if os.getenv("HF_TOKEN") else {}


def embed_batch(texts: list, retries: int = 5) -> list:
    """Chama HF Inference API com retry e backoff."""
    for attempt in range(retries):
        try:
            response = requests.post(
                API_URL,
                headers=HEADERS,
                json={"inputs": texts},
                timeout=60
            )
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                wait = 2 ** attempt
                print(f"  Rate limit, aguardando {wait}s...")
                time.sleep(wait)
            else:
                print(f"  Erro {response.status_code}: {response.text[:200]}")
                time.sleep(2 ** attempt)
        except Exception as e:
            print(f"  Erro: {e}")
            time.sleep(2 ** attempt)
    return []


def main():
    db = get_db_client()

    journals = db.execute("""
        SELECT j.id, j.title, j.scope_text
        FROM journals j
        JOIN journal_embeddings je ON je.journal_id = j.id
        ORDER BY j.id
    """, fetch=True)

    print(f"Revistas para atualizar: {len(journals)}")
    print(f"Modelo: {MODEL}")

    batch_size = 32
    sql = """
        INSERT INTO journal_embeddings (journal_id, title_embedding, abstract_embedding, model_name)
        VALUES (%s, %s::vector, %s::vector, %s)
        ON CONFLICT (journal_id) DO UPDATE SET
            title_embedding = EXCLUDED.title_embedding,
            abstract_embedding = EXCLUDED.abstract_embedding,
            model_name = EXCLUDED.model_name,
            generated_at = NOW()
    """

    for i in range(0, len(journals), batch_size):
        batch = journals[i:i + batch_size]
        titles = [j["title"] for j in batch]
        scopes = [j["scope_text"] or j["title"] for j in batch]

        title_embs = embed_batch(titles)
        abstract_embs = embed_batch(scopes)

        if not title_embs or not abstract_embs:
            print(f"  Pulando lote {i} devido a erro na API")
            continue

        params_list = [
            (
                journal["id"],
                title_embs[idx],
                abstract_embs[idx],
                MODEL
            )
            for idx, journal in enumerate(batch)
        ]

        db.executemany(sql, params_list)
        print(f"  Atualizados: {i + len(batch)}/{len(journals)}")

        # Respeita rate limit da API gratuita
        time.sleep(0.5)

    print("Atualização concluída.")


if __name__ == "__main__":
    main()

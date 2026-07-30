"""
Atualiza embeddings no banco usando fastembed (ONNX leve).
"""

import os
import sys
import argparse

# Evita symlinks no Windows (causa travamento sem permissão de admin)
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["FASTEMBED_CACHE_PATH"] = os.path.join(os.path.dirname(__file__), "..", "data", "fastembed_cache")

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db_client import get_db_client
from fastembed import TextEmbedding

MODEL = "sentence-transformers/all-MiniLM-L6-v2"
BATCH_SIZE = 128


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-batches", type=int, default=None, help="Número máximo de lotes a processar")
    return parser.parse_args()


def fetch_batch(db, last_id: int, limit: int):
    return db.execute("""
        SELECT j.id, j.title, j.scope_text
        FROM journals j
        JOIN journal_embeddings je ON je.journal_id = j.id
        WHERE j.id > %s AND je.model_name IS DISTINCT FROM %s
        ORDER BY j.id
        LIMIT %s
    """, (last_id, MODEL, limit), fetch=True)


def main():
    args = parse_args()
    print(f"[1/3] Carregando modelo fastembed: {MODEL}")
    embedder = TextEmbedding(model_name=MODEL)
    print("[2/3] Conectando ao banco...")
    db = get_db_client()

    total = db.execute(
        "SELECT COUNT(*) FROM journal_embeddings WHERE model_name IS DISTINCT FROM %s",
        (MODEL,), fetch=True
    )[0]["count"]
    print(f"[3/3] Total de embeddings pendentes: {total}")

    sql = """
        INSERT INTO journal_embeddings (journal_id, title_embedding, abstract_embedding, model_name)
        VALUES (%s, %s::vector, %s::vector, %s)
        ON CONFLICT (journal_id) DO UPDATE SET
            title_embedding = EXCLUDED.title_embedding,
            abstract_embedding = EXCLUDED.abstract_embedding,
            model_name = EXCLUDED.model_name,
            generated_at = NOW()
    """

    last_id = 0
    updated = 0
    batches = 0
    while True:
        if args.max_batches is not None and batches >= args.max_batches:
            print(f"Limite de {args.max_batches} lotes atingido. Reinicie para continuar.")
            break

        journals = fetch_batch(db, last_id, BATCH_SIZE)
        if not journals:
            print("Atualização concluída.")
            break

        titles = [j["title"] for j in journals]
        scopes = [j["scope_text"] or j["title"] for j in journals]

        title_embs = list(embedder.embed(titles))
        abstract_embs = list(embedder.embed(scopes))

        params_list = [
            (
                journal["id"],
                title_embs[idx].tolist(),
                abstract_embs[idx].tolist(),
                MODEL
            )
            for idx, journal in enumerate(journals)
        ]

        db.executemany(sql, params_list)
        updated += len(journals)
        batches += 1
        last_id = journals[-1]["id"]
        print(f"  Atualizados: {updated}/{total} (last_id={last_id})")


if __name__ == "__main__":
    main()

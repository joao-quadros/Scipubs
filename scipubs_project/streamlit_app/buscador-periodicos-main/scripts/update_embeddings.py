"""
Atualiza embeddings de todas as revistas já inseridas no banco
para o modelo sentence-transformers configurado em HybridEmbeddingService.
Versão com debug detalhado.
"""

import os
import sys
import argparse

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db_client import get_db_client
from services.hybrid_embeddings import HybridEmbeddingService


def parse_args():
    parser = argparse.ArgumentParser(description="Atualiza embeddings das revistas no banco")
    parser.add_argument("--provider", default="huggingface", choices=["gemini", "huggingface", "ollama", "tfidf"])
    parser.add_argument("--gemini-key", default=os.getenv("GEMINI_API_KEY"))
    parser.add_argument("--batch-size", type=int, default=64)
    return parser.parse_args()


def main():
    args = parse_args()

    print("[1/5] Conectando ao banco...")
    db = get_db_client()
    print("[2/5] Inicializando serviço de embeddings...")
    embedding_service = HybridEmbeddingService(
        provider=args.provider,
        gemini_api_key=args.gemini_key
    )

    print("[3/5] Carregando modelo sentence-transformers...")
    model = embedding_service._hf_model
    if model is None:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(embedding_service.huggingface_model)
    print(f"      Modelo carregado: {embedding_service.huggingface_model}")

    print("[4/5] Buscando revistas do banco...")
    journals = db.execute("""
        SELECT j.id, j.title, j.scope_text
        FROM journals j
        JOIN journal_embeddings je ON je.journal_id = j.id
        ORDER BY j.id
    """, fetch=True)
    print(f"      Revistas para atualizar: {len(journals)}")

    sql = """
        INSERT INTO journal_embeddings (journal_id, title_embedding, abstract_embedding, model_name)
        VALUES (%s, %s::vector, %s::vector, %s)
        ON CONFLICT (journal_id) DO UPDATE SET
            title_embedding = EXCLUDED.title_embedding,
            abstract_embedding = EXCLUDED.abstract_embedding,
            model_name = EXCLUDED.model_name,
            generated_at = NOW()
    """

    print("[5/5] Iniciando atualização...")
    for i in range(0, len(journals), args.batch_size):
        batch = journals[i:i + args.batch_size]
        titles = [j["title"] for j in batch]
        scopes = [j["scope_text"] or j["title"] for j in batch]

        print(f"  Lote {i}/{len(journals)}: codificando {len(batch)} títulos...")
        title_embs = model.encode(titles, normalize_embeddings=True, show_progress_bar=False)
        print(f"  Lote {i}/{len(journals)}: codificando {len(batch)} escopos...")
        abstract_embs = model.encode(scopes, normalize_embeddings=True, show_progress_bar=False)

        params_list = [
            (
                journal["id"],
                title_embs[idx].tolist(),
                abstract_embs[idx].tolist(),
                embedding_service.huggingface_model
            )
            for idx, journal in enumerate(batch)
        ]

        print(f"  Lote {i}/{len(journals)}: salvando no banco...")
        db.executemany(sql, params_list)
        print(f"  Atualizados: {i + len(batch)}/{len(journals)}")

    print("Atualização concluída.")


if __name__ == "__main__":
    main()

"""
Atualiza embeddings usando transformers + torch diretamente.
Alternativa ao sentence-transformers que estava travando no Windows.
"""

import os
import sys
import argparse
import torch
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db_client import get_db_client
from transformers import AutoTokenizer, AutoModel


def parse_args():
    parser = argparse.ArgumentParser(description="Atualiza embeddings das revistas no banco")
    parser.add_argument("--model", default="sentence-transformers/paraphrase-MiniLM-L3-v2")
    parser.add_argument("--batch-size", type=int, default=32)
    return parser.parse_args()


def mean_pooling(model_output, attention_mask):
    token_embeddings = model_output[0]
    input_mask_expanded = attention_mask.unsqueeze(-1).float()
    return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)


def embed_batch(texts: list, tokenizer, model, device: str = "cpu") -> np.ndarray:
    encoded = tokenizer(texts, padding=True, truncation=True, max_length=512, return_tensors="pt")
    encoded = {k: v.to(device) for k, v in encoded.items()}
    with torch.no_grad():
        outputs = model(**encoded)
    embeddings = mean_pooling(outputs, encoded["attention_mask"])
    embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)
    return embeddings.cpu().numpy()


def fetch_batch(db, offset: int, limit: int):
    return db.execute("""
        SELECT j.id, j.title, j.scope_text
        FROM journals j
        JOIN journal_embeddings je ON je.journal_id = j.id
        WHERE je.model_name != 'sentence-transformers/paraphrase-MiniLM-L3-v2'
        ORDER BY j.id
        LIMIT %s OFFSET %s
    """, (limit, offset), fetch=True)


def main():
    args = parse_args()

    print(f"[1/4] Carregando tokenizer e modelo: {args.model}")
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    model = AutoModel.from_pretrained(args.model)
    model.eval()
    print("[2/4] Conectando ao banco...")
    db = get_db_client()

    total = db.execute("""
        SELECT COUNT(*) FROM journal_embeddings
        WHERE model_name != 'sentence-transformers/paraphrase-MiniLM-L3-v2'
    """, fetch=True)[0]["count"]
    print(f"[3/4] Embeddings pendentes: {total}")

    sql = """
        INSERT INTO journal_embeddings (journal_id, title_embedding, abstract_embedding, model_name)
        VALUES (%s, %s::vector, %s::vector, %s)
        ON CONFLICT (journal_id) DO UPDATE SET
            title_embedding = EXCLUDED.title_embedding,
            abstract_embedding = EXCLUDED.abstract_embedding,
            model_name = EXCLUDED.model_name,
            generated_at = NOW()
    """

    offset = 0
    updated = 0
    while True:
        journals = fetch_batch(db, offset, args.batch_size)
        if not journals:
            break

        titles = [j["title"] for j in journals]
        scopes = [j["scope_text"] or j["title"] for j in journals]

        title_embs = embed_batch(titles, tokenizer, model)
        abstract_embs = embed_batch(scopes, tokenizer, model)

        params_list = [
            (
                journal["id"],
                title_embs[idx].tolist(),
                abstract_embs[idx].tolist(),
                args.model
            )
            for idx, journal in enumerate(journals)
        ]

        db.executemany(sql, params_list)
        updated += len(journals)
        print(f"  Atualizados: {updated}/{total}")
        offset += args.batch_size

    print("[4/4] Atualização concluída.")


if __name__ == "__main__":
    main()

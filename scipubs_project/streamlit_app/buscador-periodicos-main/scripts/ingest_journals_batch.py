"""
Ingestão em lotes de revistas do CSV para PostgreSQL/pgvector.
Usa batch encoding do sentence-transformers para alta velocidade.
"""

import os
import sys
import argparse
import pandas as pd
import numpy as np
from typing import List, Dict

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db_client import get_db_client
from services.hybrid_embeddings import HybridEmbeddingService


def parse_args():
    parser = argparse.ArgumentParser(description="Ingest journals from CSV in batches")
    parser.add_argument("--csv", default="dados.csv", help="Caminho do CSV de revistas")
    parser.add_argument("--provider", default="huggingface", choices=["gemini", "huggingface", "ollama", "tfidf"])
    parser.add_argument("--gemini-key", default=os.getenv("GEMINI_API_KEY"), help="Gemini API key")
    parser.add_argument("--batch-size", type=int, default=64, help="Tamanho do lote de embeddings")
    parser.add_argument("--limit", type=int, default=None, help="Limitar número total de revistas")
    parser.add_argument("--offset", type=int, default=0, help="Pular primeiras N revistas")
    return parser.parse_args()


def load_journals_csv(path: str) -> pd.DataFrame:
    with open(path, "r", encoding="utf-8-sig", errors="ignore") as f:
        primeira_linha = f.readline()
    sep = ";" if primeira_linha.count(";") >= primeira_linha.count(",") else ","

    df = pd.read_csv(path, sep=sep, encoding="utf-8-sig", low_memory=False, on_bad_lines="skip")
    df.columns = df.columns.str.replace("\ufeff", "", regex=False)
    df.columns = [c.strip() for c in df.columns]
    df.columns = [c.replace("Grande Area", "Grande Área")
                    .replace("Area do Conhecimento", "Área do Conhecimento")
                    .replace("Subarea do Conhecimento", "Subárea do Conhecimento")
                  for c in df.columns]
    return df


def parse_float(val):
    try:
        return float(str(val).replace(",", ".").strip())
    except (ValueError, TypeError):
        return None


def parse_int(val):
    try:
        return int(float(str(val).replace(",", ".").strip()))
    except (ValueError, TypeError):
        return None


def row_to_journal(row) -> Dict:
    col_titulo = row.index[0]
    title = str(row[col_titulo]).strip()

    subjects = []
    disciplines = []
    for col in ["Grande Área", "Área do Conhecimento", "Subárea do Conhecimento"]:
        if col in row.index and str(row[col]) not in ["-", "nan", "None", ""]:
            subjects.append(str(row[col]).strip())
            for part in str(row[col]).split(","):
                disciplines.append(part.strip().lower())

    indexador = str(row.get("Indexador", "")).lower()
    is_oa = "doaj" in indexador or "scielo" in indexador
    oa_type = "gold" if "doaj" in indexador else ("bronze" if "scielo" in indexador else "subscription")

    return {
        "title": title,
        "issn": str(row.get("ISSN", "")).strip() if str(row.get("ISSN", "")).strip() not in ["-", "nan", "None", ""] else None,
        "e_issn": None,
        "publisher": str(row.get("Publisher", "-")).strip() if "Publisher" in row.index else None,
        "country": str(row.get("Country", "-")).strip() if "Country" in row.index else None,
        "language": str(row.get("Idioma", "-")).strip() if "Idioma" in row.index else None,
        "subjects": subjects,
        "disciplines": list(set(disciplines)),
        "is_open_access": is_oa,
        "oa_type": oa_type,
        "apc_value_usd": None,
        "avg_days_to_first_decision": None,
        "acceptance_rate": None,
        "jif": parse_float(row.get("JIF", None)),
        "sjr": parse_float(row.get("SJR", None)),
        "quartil_jcr": str(row.get("Quartil JCR", "")).strip() if str(row.get("Quartil JCR", "")).strip() not in ["-", "nan", "None", ""] else None,
        "sjr_quartile": str(row.get("SJR Best Quartile", "")).strip() if str(row.get("SJR Best Quartile", "")).strip() not in ["-", "nan", "None", ""] else None,
        "h_index": parse_int(row.get("H index", row.get("h-index", None))),
        "h5_index": None,
        "homepage": str(row.get("Homepage", "")).strip() if str(row.get("Homepage", "")).strip() not in ["-", "nan", "None", ""] else None,
        "h5_link": str(row.get("Índice h5", "")).strip() if str(row.get("Índice h5", "")).strip() not in ["-", "nan", "None", ""] else None,
        "scope_text": " ".join(subjects + [title]).strip()
    }


def insert_journals_batch(db, journals: List[Dict], title_embs: np.ndarray, abstract_embs: np.ndarray):
    """Insere um lote de revistas e seus embeddings em uma transação."""
    db.execute("BEGIN;", fetch=False)
    try:
        for i, journal in enumerate(journals):
            try:
                journal_id = db.insert_journal(journal)
                db.insert_journal_embedding(
                    journal_id,
                    title_embs[i].tolist(),
                    abstract_embs[i].tolist(),
                    model_name="all-MiniLM-L6-v2"
                )
            except Exception as e:
                print(f"    Erro ao inserir '{journal['title'][:50]}': {e}")
        db.execute("COMMIT;", fetch=False)
    except Exception as e:
        db.execute("ROLLBACK;", fetch=False)
        raise e


def main():
    args = parse_args()

    db = get_db_client()
    embedding_service = HybridEmbeddingService(provider=args.provider, gemini_api_key=args.gemini_key)
    model = embedding_service._hf_model
    if model is None:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(embedding_service.huggingface_model)

    df = load_journals_csv(args.csv)
    print(f"Revistas no CSV: {len(df)}")

    # Aplica offset e limit
    df = df.iloc[args.offset:]
    if args.limit:
        df = df.head(args.limit)

    print(f"Processando: {len(df)} revistas (offset={args.offset}, batch_size={args.batch_size})")

    # Converte DataFrame para lista de journals
    journals = []
    for _, row in df.iterrows():
        journal = row_to_journal(row)
        if journal["title"] and journal["title"] not in ["-", "nan", "None"]:
            journals.append(journal)

    total = len(journals)
    inserted = 0

    for i in range(0, total, args.batch_size):
        if i % (args.batch_size * 10) == 0:
            print(f"  Progresso: {i}/{total} ({i/total*100:.1f}%)")
        batch = journals[i:i + args.batch_size]

        titles = [j["title"] for j in batch]
        scopes = [j["scope_text"] for j in batch]

        # Batch encoding (muito mais rápido)
        title_embs = model.encode(titles, normalize_embeddings=True, show_progress_bar=False)
        abstract_embs = model.encode(scopes, normalize_embeddings=True, show_progress_bar=False)

        insert_journals_batch(db, batch, title_embs, abstract_embs)
        inserted += len(batch)

    print(f"Ingestão concluída. Total inserido: {inserted}")


if __name__ == "__main__":
    main()

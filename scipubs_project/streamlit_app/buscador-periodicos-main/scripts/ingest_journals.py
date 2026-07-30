"""
Script de ingestão de dados do CSV local + OpenAlex para PostgreSQL/pgvector.
"""

import os
import sys
import argparse
import pandas as pd
from typing import Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db_client import get_db_client
from services.hybrid_embeddings import get_embedding_service
from services.openalex_ingestion import get_openalex_ingestion_service


def parse_args():
    parser = argparse.ArgumentParser(description="Ingest journals from CSV into pgvector")
    parser.add_argument("--csv", default="dados.csv", help="Caminho do CSV de revistas")
    parser.add_argument("--provider", default="gemini", choices=["gemini", "huggingface", "ollama", "tfidf"])
    parser.add_argument("--gemini-key", default=os.getenv("GEMINI_API_KEY"), help="Gemini API key")
    parser.add_argument("--max-articles", type=int, default=5, help="Artigos OpenAlex por revista")
    parser.add_argument("--limit", type=int, default=None, help="Limitar número de revistas")
    parser.add_argument("--init-schema", action="store_true", help="Inicializar schema antes")
    parser.add_argument("--skip-articles", action="store_true", help="Pular busca de artigos no OpenAlex")
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


def row_to_journal(row) -> dict:
    col_titulo = row.index[0]
    title = str(row[col_titulo]).strip()

    # Subjects e disciplines como arrays
    subjects = []
    disciplines = []
    for col in ["Grande Área", "Área do Conhecimento", "Subárea do Conhecimento"]:
        if col in row.index and str(row[col]) not in ["-", "nan", "None", ""]:
            subjects.append(str(row[col]).strip())
            for part in str(row[col]).split(","):
                disciplines.append(part.strip().lower())

    # Determina OA a partir do indexador
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


def main():
    args = parse_args()

    db = get_db_client()
    if args.init_schema:
        db.init_schema()

    embedding_service = get_embedding_service(provider=args.provider, gemini_api_key=args.gemini_key)
    openalex = get_openalex_ingestion_service()

    df = load_journals_csv(args.csv)
    print(f"Revistas no CSV: {len(df)}")

    if args.limit:
        df = df.head(args.limit)

    for idx, row in df.iterrows():
        journal = row_to_journal(row)
        if not journal["title"] or journal["title"] in ["-", "nan", "None"]:
            print(f"[{idx+1}] Pulando título inválido: {journal['title']}")
            continue

        print(f"[{idx+1}/{len(df)}] Processando: {journal['title'][:60]}...")

        try:
            # 1. Insere journal
            print("  -> Inserindo journal...")
            journal_id = db.insert_journal(journal)
            print(f"  -> Journal ID: {journal_id}")

            # 2. Gera embeddings do escopo
            print("  -> Gerando embeddings...")
            title_emb = embedding_service.embed_text(journal["title"]).tolist()
            abstract_emb = embedding_service.embed_text(journal["scope_text"]).tolist()
            print(f"  -> Embedding dims: title={len(title_emb)}, abstract={len(abstract_emb)}")
            print("  -> Inserindo embeddings no banco...")
            db.insert_journal_embedding(journal_id, title_emb, abstract_emb, model_name=args.provider)
            print("  -> Embeddings inseridos")

            # 3. Busca artigos no OpenAlex
            articles = []
            if not args.skip_articles:
                print("  -> Buscando artigos no OpenAlex...")
                articles = openalex.fetch_articles_for_journal(
                    journal_name=journal["title"],
                    issn=journal["issn"],
                    per_page=args.max_articles
                )
                print(f"  -> {len(articles)} artigos encontrados")

            # 4. Insere artigos com embeddings
            for art in articles:
                if not art.get("abstract"):
                    continue
                try:
                    art_title_emb = embedding_service.embed_text(art["title"]).tolist()
                    art_abstract_emb = embedding_service.embed_text(art["abstract"]).tolist()
                    article_data = {
                        "journal_id": journal_id,
                        "title": art["title"],
                        "abstract": art["abstract"],
                        "doi": art["doi"],
                        "pub_year": art["pub_year"],
                        "pub_date": art["pub_date"],
                        "citation_count": art["citation_count"],
                        "title_embedding": art_title_emb,
                        "abstract_embedding": art_abstract_emb,
                        "article_text": art["article_text"]
                    }
                    db.insert_article(article_data)
                except Exception as e:
                    print(f"    Erro ao inserir artigo {art.get('doi')}: {e}")

            print(f"[{idx+1}/{len(df)}] OK - {journal['title'][:50]}: {len(articles)} artigos")

        except Exception as e:
            import traceback
            print(f"    ERRO ao processar {journal.get('title')}: {e}")
            traceback.print_exc()

    print("Ingestão concluída.")


if __name__ == "__main__":
    main()

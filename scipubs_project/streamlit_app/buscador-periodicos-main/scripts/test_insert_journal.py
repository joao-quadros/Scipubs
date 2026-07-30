"""
Testa inserção de journal e embedding.
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db_client import get_db_client


def main():
    db = get_db_client()

    journal = {
        "title": "TESTE MANUAL CLIENT",
        "issn": None,
        "e_issn": None,
        "publisher": "Teste",
        "country": "BR",
        "language": "PT",
        "subjects": ["Teste"],
        "disciplines": ["teste"],
        "is_open_access": False,
        "oa_type": "subscription",
        "apc_value_usd": None,
        "avg_days_to_first_decision": None,
        "acceptance_rate": None,
        "jif": None,
        "sjr": None,
        "quartil_jcr": None,
        "sjr_quartile": None,
        "h_index": None,
        "h5_index": None,
        "homepage": None,
        "h5_link": None,
        "scope_text": "teste"
    }

    jid = db.insert_journal(journal)
    print(f"Journal ID retornado: {jid}")

    result = db.execute("SELECT COUNT(*) AS n FROM journals WHERE id = %s", (jid,), fetch=True)
    print(f"Count após insert na mesma conexão: {result[0]['n']}")

    # Testa embedding
    emb = [0.0] * 768
    db.insert_journal_embedding(jid, emb, emb, model_name="tfidf")
    print("Embedding inserido")


if __name__ == "__main__":
    main()

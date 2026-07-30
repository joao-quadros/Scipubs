"""
Conta registros nas tabelas do banco.
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db_client import get_db_client


def main():
    db = get_db_client()
    tables = ["journals", "journal_articles", "journal_embeddings"]
    for table in tables:
        try:
            result = db.execute(f"SELECT COUNT(*) AS n FROM {table};", fetch=True)
            print(f"{table}: {result[0]['n']}")
        except Exception as e:
            print(f"{table}: erro - {e}")


if __name__ == "__main__":
    main()

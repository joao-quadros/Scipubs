"""
Diagnóstico do banco de dados.
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db_client import get_db_client


def main():
    db = get_db_client()

    print("=== TABELAS ===")
    result = db.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name;",
        fetch=True
    )
    for row in result:
        print(f"  - {row['table_name']}")

    print("\n=== COLUNAS DA TABELA journals ===")
    result = db.execute(
        "SELECT column_name, data_type FROM information_schema.columns WHERE table_name='journals' ORDER BY ordinal_position;",
        fetch=True
    )
    for row in result:
        print(f"  {row['column_name']}: {row['data_type']}")

    print("\n=== TRIGGERS ===")
    result = db.execute(
        "SELECT trigger_name, event_object_table FROM information_schema.triggers WHERE trigger_schema='public';",
        fetch=True
    )
    for row in result:
        print(f"  {row['trigger_name']} on {row['event_object_table']}")

    print("\n=== SEQUENCES ===")
    result = db.execute(
        "SELECT sequence_name FROM information_schema.sequences WHERE sequence_schema='public';",
        fetch=True
    )
    for row in result:
        print(f"  {row['sequence_name']}")

    print("\n=== COUNT journals ===")
    result = db.execute("SELECT COUNT(*) AS n FROM journals;", fetch=True)
    print(f"  {result[0]['n']}")


if __name__ == "__main__":
    main()

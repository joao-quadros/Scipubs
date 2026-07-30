"""
Verifica se o schema foi criado corretamente no PostgreSQL.
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db_client import get_db_client


def main():
    db = get_db_client()
    print("Tabelas no banco:")
    result = db.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name;",
        fetch=True
    )
    for r in result:
        print(f"  - {r['table_name']}")

    print("\nFunções criadas:")
    result = db.execute(
        "SELECT routine_name FROM information_schema.routines WHERE routine_schema='public' ORDER BY routine_name;",
        fetch=True
    )
    for r in result:
        print(f"  - {r['routine_name']}")


if __name__ == "__main__":
    main()

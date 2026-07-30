"""
Remove dados de teste do banco.
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db_client import get_db_client


def main():
    db = get_db_client()
    db.execute("DELETE FROM journals WHERE title LIKE 'PERSIST_TEST%' OR title LIKE 'TESTE%' OR title LIKE 'TEST %';")
    print("Dados de teste removidos")


if __name__ == "__main__":
    main()

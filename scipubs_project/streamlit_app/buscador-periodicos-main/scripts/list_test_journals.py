"""
Lista journals de teste inseridos.
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db_client import get_db_client


def main():
    db = get_db_client()
    result = db.execute(
        "SELECT id, title, created_at FROM journals WHERE title LIKE 'TESTE%' ORDER BY id DESC LIMIT 10;",
        fetch=True
    )
    print("Journals de teste:")
    for row in result:
        print(f"  {row['id']} | {row['title']} | {row['created_at']}")


if __name__ == "__main__":
    main()

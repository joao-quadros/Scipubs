"""
Testa persistência de dados no banco.
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
from psycopg2.extras import RealDictCursor


def main():
    dsn = os.environ["DATABASE_URL"]
    print(f"DSN: {dsn.split('@')[1]}")

    # Conexão 1: insert e commit
    conn1 = psycopg2.connect(dsn)
    print("Conexão 1 aberta")
    print("In recovery?", conn1.info)

    with conn1.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT current_database() AS db, pg_is_in_recovery() AS recovery;")
        print(cur.fetchone())

        cur.execute("INSERT INTO journals (title, normalized_title, is_open_access, oa_type, scope_text) VALUES ('PERSIST_TEST', 'persist_test', false, 'subscription', 'test') RETURNING id;")
        jid = cur.fetchone()["id"]
        print(f"Inserido ID: {jid}")
        conn1.commit()
        print("Commit realizado")

        cur.execute("SELECT COUNT(*) AS n FROM journals WHERE id = %s;", (jid,))
        print(f"Count na conexão 1: {cur.fetchone()['n']}")
    conn1.close()

    # Conexão 2: verifica se existe
    conn2 = psycopg2.connect(dsn)
    print("Conexão 2 aberta")
    with conn2.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT COUNT(*) AS n FROM journals WHERE id = %s;", (jid,))
        print(f"Count na conexão 2: {cur.fetchone()['n']}")
        cur.execute("SELECT id, title, created_at FROM journals WHERE id = %s;", (jid,))
        print(f"Row: {cur.fetchone()}")
    conn2.close()


if __name__ == "__main__":
    main()

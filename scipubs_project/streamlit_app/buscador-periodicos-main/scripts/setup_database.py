"""
Script de setup do banco de dados.
Cria o schema pgvector no PostgreSQL configurado em DATABASE_URL.
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db_client import get_db_client


def main():
    print("Inicializando schema pgvector...")
    db = get_db_client()
    db.init_schema("sql/pgvector_schema_v2.sql")
    print("Schema criado com sucesso.")


if __name__ == "__main__":
    main()

"""
Script de migração: recria o schema com embeddings de 384 dimensões.
ATENÇÃO: remove todos os dados existentes (journals, embeddings, artigos).
Use apenas se puder re-ingerir os dados depois.
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db_client import get_db_client


def main():
    db = get_db_client()
    print("AVISO: Esta migração vai remover todos os dados do banco e recriar as tabelas com vector(384).")
    confirm = input("Digite RECRIAR para continuar: ")
    if confirm.strip().upper() != "RECRIAR":
        print("Migração cancelada.")
        return

    print("Dropando tabelas antigas...")
    db.execute("""
        DROP TABLE IF EXISTS journal_articles CASCADE;
        DROP TABLE IF EXISTS journal_embeddings CASCADE;
        DROP TABLE IF EXISTS journals CASCADE;
        DROP TABLE IF EXISTS matcher_config CASCADE;
    """, fetch=False)

    print("Recriando schema...")
    db.init_schema("sql/pgvector_schema_v2.sql")
    print("Migração concluída. O banco agora usa embeddings de 384 dimensões.")


if __name__ == "__main__":
    main()

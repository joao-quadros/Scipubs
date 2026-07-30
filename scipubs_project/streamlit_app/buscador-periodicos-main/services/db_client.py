"""
PostgreSQL Database Client
Conexão com PostgreSQL + pgvector usando psycopg2.
Compatível com Supabase e Neon (free tier).
"""

import os
from typing import List, Dict, Optional, Any
import psycopg2
from psycopg2.extras import RealDictCursor
import numpy as np
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PostgresClient:
    """Cliente PostgreSQL para Scientific Journal Recommender"""

    def __init__(self, dsn: Optional[str] = None):
        """
        Inicializa cliente PostgreSQL.

        Args:
            dsn: Connection string. Se None, usa DATABASE_URL das env vars.
        """
        self.dsn = dsn or os.getenv("DATABASE_URL")
        if not self.dsn:
            raise ValueError("DATABASE_URL não configurada")
        self._conn = None

    def _connect(self):
        """Cria conexão com o banco"""
        if self._conn is None or self._conn.closed:
            self._conn = psycopg2.connect(self.dsn, connect_timeout=10)
        return self._conn

    def execute(self, sql: str, params: Optional[tuple] = None, fetch: bool = False) -> Optional[List[Dict]]:
        """Executa query SQL genérica"""
        conn = self._connect()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, params)
                if fetch:
                    return cur.fetchall()
                conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Erro no execute: {e}")
            raise

    def executemany(self, sql: str, params_list: List[tuple]) -> None:
        """Executa query SQL em lote em uma única transação"""
        conn = self._connect()
        try:
            with conn.cursor() as cur:
                cur.executemany(sql, params_list)
                conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Erro no executemany: {e}")
            raise

    def close(self):
        """Fecha conexão persistente"""
        if getattr(self, "_conn", None) and not self._conn.closed:
            self._conn.close()
            self._conn = None

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass

    def init_schema(self, schema_path: str = "sql/pgvector_schema_v2.sql"):
        """Executa arquivo SQL de schema"""
        with open(schema_path, "r", encoding="utf-8") as f:
            sql = f.read()
        self.execute(sql)
        logger.info("Schema inicializado com sucesso")

    # =============================================================================
    # INSERTS
    # =============================================================================

    def insert_journal(self, journal: Dict[str, Any]) -> int:
        """
        Insere ou atualiza uma revista.

        Args:
            journal: Dict com campos da tabela journals

        Returns:
            ID da revista
        """
        sql = """
        INSERT INTO journals (
            title, normalized_title, issn, e_issn, publisher, country, language,
            subjects, disciplines, is_open_access, oa_type, apc_value_usd,
            avg_days_to_first_decision, acceptance_rate, jif, sjr,
            quartil_jcr, sjr_quartile, h_index, h5_index, homepage, h5_link, scope_text
        ) VALUES (
            %(title)s, LOWER(%(title)s), %(issn)s, %(e_issn)s, %(publisher)s, %(country)s, %(language)s,
            %(subjects)s, %(disciplines)s, %(is_open_access)s, %(oa_type)s, %(apc_value_usd)s,
            %(avg_days_to_first_decision)s, %(acceptance_rate)s, %(jif)s, %(sjr)s,
            %(quartil_jcr)s, %(sjr_quartile)s, %(h_index)s, %(h5_index)s, %(homepage)s, %(h5_link)s, %(scope_text)s
        )
        ON CONFLICT (issn) DO UPDATE SET
            title = EXCLUDED.title,
            normalized_title = EXCLUDED.normalized_title,
            scope_text = EXCLUDED.scope_text,
            updated_at = NOW()
        RETURNING id
        """
        result = self.execute(sql, journal, fetch=True)
        return result[0]["id"]

    def insert_journal_embedding(self, journal_id: int, title_embedding: List[float],
                                  abstract_embedding: List[float], model_name: str = "BAAI/bge-m3"):
        """Insere embeddings de uma revista"""
        sql = """
        INSERT INTO journal_embeddings (journal_id, title_embedding, abstract_embedding, model_name)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (journal_id) DO UPDATE SET
            title_embedding = EXCLUDED.title_embedding,
            abstract_embedding = EXCLUDED.abstract_embedding,
            model_name = EXCLUDED.model_name,
            generated_at = NOW()
        """
        self.execute(sql, (journal_id, title_embedding, abstract_embedding, model_name))

    def insert_article(self, article: Dict[str, Any]) -> int:
        """Insere ou atualiza um artigo"""
        sql = """
        INSERT INTO journal_articles (
            journal_id, title, abstract, doi, pub_year, pub_date, citation_count,
            title_embedding, abstract_embedding, article_text
        ) VALUES (
            %(journal_id)s, %(title)s, %(abstract)s, %(doi)s, %(pub_year)s, %(pub_date)s, %(citation_count)s,
            %(title_embedding)s, %(abstract_embedding)s, %(article_text)s
        )
        ON CONFLICT (doi) DO UPDATE SET
            title = EXCLUDED.title,
            abstract = EXCLUDED.abstract,
            article_text = EXCLUDED.article_text,
            updated_at = NOW()
        RETURNING id
        """
        result = self.execute(sql, article, fetch=True)
        return result[0]["id"]

    # =============================================================================
    # SEARCH
    # =============================================================================

    def score_journals(
        self,
        title_embedding: List[float],
        abstract_embedding: List[float],
        query_text: str,
        limit: int = 10,
        min_year: Optional[int] = None,
        max_apc_usd: Optional[float] = None,
        max_decision_days: Optional[int] = None,
        require_oa: bool = False
    ) -> List[Dict]:
        """
        Chama a função score_journals do banco e retorna revistas ranqueadas.

        Args:
            title_embedding: Embedding do título do artigo do usuário
            abstract_embedding: Embedding do abstract do artigo do usuário
            query_text: Texto bruto para sparse search
            limit: Número de resultados
            min_year: Ano mínimo de publicação dos artigos
            max_apc_usd: Filtro hard de APC
            max_decision_days: Filtro hard de tempo de decisão
            require_oa: Se True, só retorna OA

        Returns:
            Lista de dicts com scores e metadados
        """
        sql = """
        SELECT * FROM score_journals(
            %s::vector(384),
            %s::vector(384),
            %s,
            %s,
            %s,
            %s,
            %s,
            %s
        )
        """
        params = (
            title_embedding,
            abstract_embedding,
            query_text,
            limit,
            min_year,
            max_apc_usd,
            max_decision_days,
            require_oa
        )
        return self.execute(sql, params, fetch=True)

    def get_journal_by_id(self, journal_id: int) -> Optional[Dict]:
        """Busca revista completa por ID"""
        sql = "SELECT * FROM journals WHERE id = %s"
        result = self.execute(sql, (journal_id,), fetch=True)
        return result[0] if result else None

    def get_top_articles_for_journal(
        self,
        journal_id: int,
        title_embedding: List[float],
        abstract_embedding: List[float],
        query_text: str,
        limit: int = 5
    ) -> List[Dict]:
        """Busca artigos mais relevantes de uma revista para a query"""
        sql = """
        SELECT * FROM hybrid_article_search_rrf(
            %s::vector(384),
            %s::vector(384),
            %s,
            %s,
            NULL
        )
        WHERE journal_id = %s
        """
        return self.execute(sql, (title_embedding, abstract_embedding, query_text, limit, journal_id), fetch=True)


def get_db_client() -> PostgresClient:
    """Factory padrão"""
    return PostgresClient()

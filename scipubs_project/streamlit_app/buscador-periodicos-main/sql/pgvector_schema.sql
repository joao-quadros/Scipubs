-- =============================================================================
-- Schema pgvector para Hybrid Scientific Matching Formula
-- Banco: PostgreSQL 15+ com extensão pgvector
-- Provedores recomendados: Neon (free tier) ou Supabase (free tier)
-- =============================================================================

-- Habilita extensões necessárias
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "vector";

-- =============================================================================
-- 1. TABELA DE REVISTAS (metadados estáticos + business metadata)
-- =============================================================================
CREATE TABLE IF NOT EXISTS journals (
    id              SERIAL PRIMARY KEY,
    title           TEXT NOT NULL,
    normalized_title TEXT NOT NULL,
    issn            VARCHAR(20),
    e_issn          VARCHAR(20),
    publisher       TEXT,
    country         VARCHAR(100),
    language        VARCHAR(50),
    subjects        TEXT[],                       -- Array de áreas/subáreas CNPq
    disciplines     TEXT[],                       -- Array de palavras-chave do escopo

    -- Business Metadata
    apc_value_usd   NUMERIC(10,2),                -- APC em USD (0 = gratuito)
    apc_currency    VARCHAR(10) DEFAULT 'USD',
    open_access_status VARCHAR(50),               -- 'gold', 'hybrid', 'bronze', 'subscription'
    avg_days_to_first_decision INTEGER,           -- Média de dias até primeira decisão
    acceptance_rate NUMERIC(5,2),                 -- Taxa de aceitação estimada (%)
    review_time_weeks INTEGER,                    -- Tempo médio de revisão em semanas

    -- Métricas de impacto
    jif             NUMERIC(8,4),                 -- Journal Impact Factor
    sjr             NUMERIC(8,4),                 -- SCImago Journal Rank
    quartil_jcr     VARCHAR(10),                  -- Q1, Q2, Q3, Q4
    sjr_quartile    VARCHAR(10),                  -- Q1, Q2, Q3, Q4
    h_index         INTEGER,
    h5_index        INTEGER,
    homepage        TEXT,
    h5_link         TEXT,

    -- Controle
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW(),

    CONSTRAINT uq_journals_issn UNIQUE (issn)
);

CREATE INDEX IF NOT EXISTS idx_journals_title_trgm ON journals USING gin (normalized_title gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_journals_subjects ON journals USING gin (subjects);
CREATE INDEX IF NOT EXISTS idx_journals_disciplines ON journals USING gin (disciplines);

-- =============================================================================
-- 2. TABELA DE EMBEDDINGS DA REVISTA (vetor combinado escopo editorial)
-- =============================================================================
CREATE TABLE IF NOT EXISTS journal_embeddings (
    id              SERIAL PRIMARY KEY,
    journal_id      INTEGER NOT NULL REFERENCES journals(id) ON DELETE CASCADE,

    -- Vetores densos (768 dimensões para bge-m3)
    title_embedding  vector(768),
    abstract_embedding vector(768),
    scope_embedding  vector(768),                 -- Média ponderada do escopo editorial

    -- Modelo e versão do embedding
    model_name       VARCHAR(100) DEFAULT 'BAAI/bge-m3',
    generated_at     TIMESTAMP DEFAULT NOW(),

    CONSTRAINT uq_journal_embeddings_journal UNIQUE (journal_id)
);

-- Índices HNSW para busca vetorial rápida (cosine similarity)
CREATE INDEX IF NOT EXISTS idx_journal_embeddings_title_hnsw
    ON journal_embeddings USING hnsw (title_embedding vector_cosine_ops);

CREATE INDEX IF NOT EXISTS idx_journal_embeddings_scope_hnsw
    ON journal_embeddings USING hnsw (scope_embedding vector_cosine_ops);

-- =============================================================================
-- 3. TABELA DE ARTIGOS PUBLICADOS PELAS REVISTAS (para Recency + Semantic)
-- =============================================================================
CREATE TABLE IF NOT EXISTS journal_articles (
    id              BIGSERIAL PRIMARY KEY,
    journal_id      INTEGER NOT NULL REFERENCES journals(id) ON DELETE CASCADE,

    title           TEXT NOT NULL,
    abstract        TEXT,
    doi             VARCHAR(255),
    pub_year        INTEGER NOT NULL,
    pub_date        DATE,

    -- Embeddings individuais do artigo
    title_embedding vector(768),
    abstract_embedding vector(768),

    -- Termos técnicos extraídos (para BM25 / sparse retrieval)
    keywords        TEXT[],
    technical_terms TEXT[],

    -- Métricas do artigo
    citation_count  INTEGER DEFAULT 0,
    open_access     BOOLEAN DEFAULT FALSE,

    created_at      TIMESTAMP DEFAULT NOW(),

    CONSTRAINT uq_journal_articles_doi UNIQUE (doi)
);

CREATE INDEX IF NOT EXISTS idx_articles_journal_id ON journal_articles(journal_id);
CREATE INDEX IF NOT EXISTS idx_articles_pub_year ON journal_articles(pub_year);
CREATE INDEX IF NOT EXISTS idx_articles_keywords ON journal_articles USING gin (keywords);
CREATE INDEX IF NOT EXISTS idx_articles_technical_terms ON journal_articles USING gin (technical_terms);

-- Índice HNSW para artigos
CREATE INDEX IF NOT EXISTS idx_articles_title_embedding_hnsw
    ON journal_articles USING hnsw (title_embedding vector_cosine_ops);

CREATE INDEX IF NOT EXISTS idx_articles_abstract_embedding_hnsw
    ON journal_articles USING hnsw (abstract_embedding vector_cosine_ops);

-- =============================================================================
-- 4. TABELA DE TERMOS TÉCNICOS DO ESCOPO (BM25 / sparse search)
-- =============================================================================
CREATE TABLE IF NOT EXISTS journal_scope_terms (
    id              BIGSERIAL PRIMARY KEY,
    journal_id      INTEGER NOT NULL REFERENCES journals(id) ON DELETE CASCADE,
    term            VARCHAR(255) NOT NULL,
    term_type       VARCHAR(50),                  -- 'keyword', 'method', 'concept', 'discipline'
    frequency       INTEGER DEFAULT 1,            -- Frequência no escopo
    weight          NUMERIC(4,3) DEFAULT 1.0,     -- Peso do termo

    CONSTRAINT uq_journal_scope_terms UNIQUE (journal_id, term)
);

CREATE INDEX IF NOT EXISTS idx_scope_terms_term ON journal_scope_terms(term);
CREATE INDEX IF NOT EXISTS idx_scope_terms_journal ON journal_scope_terms(journal_id);

-- =============================================================================
-- 5. FUNÇÃO DE BUSCA HÍBRIDA (Dense + BM25 combinados)
-- =============================================================================
CREATE OR REPLACE FUNCTION hybrid_journal_search(
    p_query_embedding vector(768),
    p_query_terms     TEXT[],
    p_limit           INTEGER DEFAULT 20,
    p_min_pub_year    INTEGER DEFAULT NULL
)
RETURNS TABLE (
    journal_id          INTEGER,
    title               TEXT,
    semantic_score      NUMERIC,
    bm25_score          NUMERIC,
    hybrid_score        NUMERIC,
    recent_article_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    WITH dense_scores AS (
        SELECT
            je.journal_id,
            1 - (je.scope_embedding <=> p_query_embedding) AS cosine_sim
        FROM journal_embeddings je
        ORDER BY je.scope_embedding <=> p_query_embedding
        LIMIT p_limit * 3
    ),
    sparse_scores AS (
        SELECT
            jst.journal_id,
            SUM(jst.weight * jst.frequency)::NUMERIC AS term_score
        FROM journal_scope_terms jst
        WHERE jst.term = ANY(p_query_terms)
        GROUP BY jst.journal_id
    ),
    recent_articles AS (
        SELECT
            ja.journal_id,
            COUNT(*) AS recent_count
        FROM journal_articles ja
        WHERE (p_min_pub_year IS NULL OR ja.pub_year >= p_min_pub_year)
        GROUP BY ja.journal_id
    )
    SELECT
        j.id,
        j.title,
        ds.cosine_sim::NUMERIC AS semantic_score,
        COALESCE(ss.term_score, 0)::NUMERIC AS bm25_score,
        (
            (ds.cosine_sim * 0.65) +
            (COALESCE(ss.term_score, 0) / NULLIF((SELECT MAX(term_score) FROM sparse_scores), 0) * 0.35)
        )::NUMERIC AS hybrid_score,
        COALESCE(ra.recent_count, 0)::BIGINT AS recent_article_count
    FROM dense_scores ds
    JOIN journals j ON j.id = ds.journal_id
    LEFT JOIN sparse_scores ss ON ss.journal_id = ds.journal_id
    LEFT JOIN recent_articles ra ON ra.journal_id = ds.journal_id
    ORDER BY hybrid_score DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- 6. VIEW PARA RANKING FINAL COM BUSINESS METADATA
-- =============================================================================
CREATE OR REPLACE VIEW v_journal_match_ready AS
SELECT
    j.id,
    j.title,
    j.issn,
    j.publisher,
    j.subjects,
    j.apc_value_usd,
    j.open_access_status,
    j.avg_days_to_first_decision,
    j.acceptance_rate,
    j.jif,
    j.sjr,
    j.quartil_jcr,
    j.sjr_quartile,
    j.h_index,
    j.h5_index,
    j.homepage,
    j.h5_link,
    je.scope_embedding,
    je.title_embedding
FROM journals j
LEFT JOIN journal_embeddings je ON je.journal_id = j.id;

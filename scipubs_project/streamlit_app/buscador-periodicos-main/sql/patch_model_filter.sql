-- Patch: filtra embeddings para usar apenas all-MiniLM-L6-v2 (evita comparar modelos diferentes)

CREATE OR REPLACE FUNCTION dense_journal_search(
    p_query_embedding vector(384),
    p_limit INTEGER DEFAULT 100
)
RETURNS TABLE (
    journal_id      INTEGER,
    title           TEXT,
    issn            VARCHAR(20),
    cosine_score    DOUBLE PRECISION
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        j.id AS journal_id,
        j.title,
        j.issn,
        (1 - (je.abstract_embedding <=> p_query_embedding))::DOUBLE PRECISION AS cosine_score
    FROM journals j
    JOIN journal_embeddings je ON je.journal_id = j.id
    WHERE je.model_name = 'sentence-transformers/all-MiniLM-L6-v2'
    ORDER BY je.abstract_embedding <=> p_query_embedding
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

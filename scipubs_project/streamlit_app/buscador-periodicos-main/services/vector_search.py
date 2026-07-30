"""
Vector Search
Busca vetorial por similaridade de cosseno no catálogo de periódicos.
"""

import numpy as np
import pandas as pd
import os
import pickle
import logging
from typing import List, Dict, Tuple, Optional

from services.embeddings_client import EmbeddingsClient, cosine_similarity, get_embeddings_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JournalVectorSearch:
    """Busca vetorial de revistas por similaridade semântica"""

    def __init__(
        self,
        df_local: pd.DataFrame,
        embeddings_client: Optional[EmbeddingsClient] = None,
        cache_dir: str = "data"
    ):
        """
        Inicializa a busca vetorial

        Args:
            df_local: DataFrame com base local de revistas
            embeddings_client: Cliente de embeddings
            cache_dir: Diretório para cache dos embeddings
        """
        self.df_local = df_local.copy()
        self.col_titulo = df_local.columns[0]
        self.embeddings_client = embeddings_client or get_embeddings_client()
        self.cache_dir = cache_dir
        self.vectors = None
        self.catalog_texts = []
        self._build_catalog_texts()
        self._load_or_compute_vectors()

    def _build_catalog_texts(self):
        """Constrói textos representativos de cada revista"""
        texts = []
        for _, row in self.df_local.iterrows():
            partes = [str(row[self.col_titulo])]
            for col in ["Grande Área", "Área do Conhecimento", "Subárea do Conhecimento"]:
                if col in row.index:
                    val = str(row[col])
                    if val and val not in ["-", "nan", "None", ""]:
                        partes.append(val)
            texts.append(" ".join(partes))
        self.catalog_texts = texts

    def _cache_path(self) -> str:
        """Caminho do arquivo de cache de embeddings"""
        os.makedirs(self.cache_dir, exist_ok=True)
        return os.path.join(self.cache_dir, "journal_vectors.pkl")

    def _load_or_compute_vectors(self):
        """Carrega embeddings do cache ou computa do zero"""
        cache_path = self._cache_path()

        if os.path.exists(cache_path):
            try:
                with open(cache_path, "rb") as f:
                    data = pickle.load(f)
                    self.vectors = data["vectors"]
                    cached_texts = data.get("texts", [])
                    if len(cached_texts) == len(self.catalog_texts):
                        logger.info(f"Embeddings carregados do cache: {len(self.vectors)} revistas")
                        return
            except Exception as e:
                logger.warning(f"Erro ao carregar cache de embeddings: {e}")

        logger.info("Computando embeddings do catálogo...")
        self.embeddings_client.fit_tfidf(self.catalog_texts)
        self.vectors = self.embeddings_client.embed_batch(self.catalog_texts)

        try:
            with open(cache_path, "wb") as f:
                pickle.dump({"vectors": self.vectors, "texts": self.catalog_texts}, f)
            logger.info("Embeddings salvos em cache")
        except Exception as e:
            logger.warning(f"Erro ao salvar cache de embeddings: {e}")

    def search(self, query_text: str, top_k: int = 40) -> List[Dict]:
        """
        Busca as revistas mais similares ao texto de consulta

        Args:
            query_text: Texto de consulta (título + resumo)
            top_k: Número de resultados

        Returns:
            Lista de dicionários com revista e score de similaridade
        """
        query_vector = self.embeddings_client.embed(query_text)

        similarities = []
        for idx, vec in enumerate(self.vectors):
            sim = cosine_similarity(query_vector, vec)
            similarities.append((idx, sim))

        # Ordena por similaridade decrescente
        similarities.sort(key=lambda x: x[1], reverse=True)

        results = []
        for idx, sim in similarities[:top_k]:
            row = self.df_local.iloc[idx]
            results.append({
                "nome": str(row[self.col_titulo]),
                "issn": str(row.get("ISSN", "-")),
                "homepage": str(row.get("Homepage", "-")),
                "grande_area": str(row.get("Grande Área", "-")),
                "area": str(row.get("Área do Conhecimento", row.get("Area do Conhecimento", "-"))),
                "subarea": str(row.get("Subárea do Conhecimento", "-")),
                "indexador": str(row.get("Indexador", "-")),
                "jif": row.get("JIF", "-"),
                "quartil_jcr": str(row.get("Quartil JCR", "-")),
                "sjr": row.get("SJR", "-"),
                "sjr_quartile": str(row.get("SJR Best Quartile", "-")),
                "h_index": row.get("H index", row.get("h-index", "-")),
                "h5_link": str(row.get("Índice h5", "-")),
                "similaridade": sim,
                "aderencia": round(sim * 100, 1),
                "fonte_dados": "local",
            })

        return results


def get_vector_search(df_local: pd.DataFrame, embeddings_client: Optional[EmbeddingsClient] = None) -> JournalVectorSearch:
    """Retorna instância da busca vetorial"""
    return JournalVectorSearch(df_local=df_local, embeddings_client=embeddings_client)

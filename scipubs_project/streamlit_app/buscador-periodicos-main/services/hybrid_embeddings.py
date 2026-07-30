"""
Hybrid Embeddings Service
Gera embeddings densos com peso 1.5 para título e 1.0 para abstract.
Suporta múltiplos providers: Gemini (gratuito), Hugging Face (bge-m3), Ollama local.
"""

import os
import re
import numpy as np
from typing import List, Optional, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HybridEmbeddingService:
    """
    Serviço de embeddings híbridos para scientific journal matching.
    Peso do título: 1.5
    Peso do abstract: 1.0
    """

    DEFAULT_HF_MODEL = "sentence-transformers/all-MiniLM-L6-v2"  # 384 dimensões, ONNX via fastembed, ~90MB

    def __init__(
        self,
        provider: str = "gemini",  # 'gemini', 'huggingface', 'ollama', 'tfidf'
        model_name: str = "embedding-001",
        gemini_api_key: Optional[str] = None,
        ollama_model: str = "nomic-embed-text",
        huggingface_model: str = DEFAULT_HF_MODEL,
        embedding_dim: int = 384
    ):
        self.provider = provider
        self.model_name = model_name
        self.gemini_api_key = gemini_api_key
        self.ollama_model = ollama_model
        self.huggingface_model = huggingface_model
        self.embedding_dim = embedding_dim
        self._hf_model = None  # sentence-transformers fallback
        self._fastembed_model = None  # fastembed (preferido)

    def _normalize(self, vector: np.ndarray) -> np.ndarray:
        """Normaliza vetor para norma 1"""
        norm = np.linalg.norm(vector)
        if norm == 0:
            return vector
        return vector / norm

    def embed_text(self, text: str) -> np.ndarray:
        """Gera embedding de um texto puro"""
        text = text.strip()
        if not text:
            return np.zeros(self.embedding_dim, dtype=np.float32)

        if self.provider == "gemini":
            try:
                return self._embed_gemini(text)
            except Exception as e:
                logger.warning(f"Erro ao usar Gemini embeddings: {e}. Usando fallback TF-IDF.")
                return self._fallback_embed(text)
        elif self.provider == "huggingface":
            return self._embed_huggingface(text)
        elif self.provider == "sentence-transformers":
            return self._embed_huggingface(text)
        elif self.provider == "ollama":
            return self._embed_ollama(text)
        elif self.provider == "tfidf":
            return self._fallback_embed(text)
        else:
            raise ValueError(f"Provider desconhecido: {self.provider}")

    def embed_query(self, title: str, abstract: str) -> np.ndarray:
        """
        Combina embedding do título (peso 1.5) com abstract (peso 1.0).
        Retorna vetor normalizado.
        """
        title_vec = self.embed_text(title) * 1.5
        abstract_vec = self.embed_text(abstract) * 1.0
        combined = title_vec + abstract_vec
        return self._normalize(combined).astype(np.float32)

    def embed_journal_scope(
        self,
        journal_title: str,
        journal_description: str,
        sample_articles: List[Dict[str, str]]
    ) -> Dict[str, np.ndarray]:
        """
        Gera embeddings para uma revista:
        - title_embedding: título da revista
        - abstract_embedding: descrição/escopo
        - scope_embedding: média ponderada de título (1.5) + descrição (1.0) + amostras de artigos (0.5 cada)
        """
        title_vec = self.embed_text(journal_title) * 1.5
        desc_vec = self.embed_text(journal_description) * 1.0

        article_vectors = []
        for art in sample_articles[:10]:  # Máximo 10 artigos
            art_title = art.get("title", "")
            art_abstract = art.get("abstract", "")
            art_vec = self.embed_query(art_title, art_abstract) * 0.5
            article_vectors.append(art_vec)

        scope_vec = title_vec + desc_vec
        if article_vectors:
            scope_vec += np.mean(article_vectors, axis=0)

        return {
            "title_embedding": self._normalize(title_vec).astype(np.float32),
            "abstract_embedding": self._normalize(desc_vec).astype(np.float32),
            "scope_embedding": self._normalize(scope_vec).astype(np.float32),
        }

    def extract_technical_terms(self, text: str) -> List[str]:
        """
        Extrai termos técnicos candidatos para BM25/sparse search.
        Remove stopwords e mantém n-gramas técnicos.
        """
        stopwords = {
            "the", "and", "of", "in", "to", "a", "an", "for", "with", "on", "is", "are", "was", "were",
            "o", "a", "os", "as", "um", "uma", "de", "do", "da", "dos", "das", "e", "ou", "em", "para",
            "por", "com", "sem", "sobre", "este", "esta", "esse", "essa", "artigo", "article", "study",
            "estudo", "research", "pesquisa", "using", "use", "used", "based"
        }

        text = re.sub(r"[^a-zA-Z0-9\s\-]", " ", text)
        tokens = [t.lower().strip("-") for t in text.split() if len(t) > 2]
        terms = [t for t in tokens if t not in stopwords]

        # Bigramas técnicos conhecidos (ex: machine learning, crisper-cas9)
        bigrams = []
        for i in range(len(tokens) - 1):
            b = f"{tokens[i]} {tokens[i+1]}"
            if tokens[i] not in stopwords and tokens[i+1] not in stopwords:
                bigrams.append(b)

        return list(set(terms + bigrams))

    # ===========================
    # Providers
    # ===========================

    def _embed_gemini(self, text: str) -> np.ndarray:
        """Embedding via Google Gemini API (gratuito com limite generoso)"""
        import requests

        if not self.gemini_api_key:
            raise ValueError("Chave Gemini não fornecida para provider 'gemini'")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:embedContent?key={self.gemini_api_key}"
        payload = {
            "content": {"parts": [{"text": text[:8000]}]},
            "taskType": "RETRIEVAL_QUERY"
        }
        response = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=30)
        response.raise_for_status()
        values = response.json()["embedding"]["values"]
        return np.array(values, dtype=np.float32)

    def _embed_huggingface(self, text: str) -> np.ndarray:
        """Embedding via fastembed ONNX (leve, gratuito, sem API). Fallback para sentence-transformers."""
        try:
            from fastembed import TextEmbedding
            if self._fastembed_model is None:
                logger.info(f"Carregando modelo fastembed: {self.huggingface_model}")
                self._fastembed_model = TextEmbedding(model_name=self.huggingface_model)
            vector = list(self._fastembed_model.embed([text[:8000]]))[0]
            return np.array(vector, dtype=np.float32)
        except ImportError:
            logger.warning("fastembed não instalado. Usando sentence-transformers como fallback.")
            return self._embed_sentence_transformers(text)
        except Exception as e:
            logger.warning(f"Erro no fastembed: {e}. Fallback para sentence-transformers.")
            return self._embed_sentence_transformers(text)

    def _embed_sentence_transformers(self, text: str) -> np.ndarray:
        """Fallback usando sentence-transformers"""
        from sentence_transformers import SentenceTransformer
        if self._hf_model is None:
            logger.info(f"Carregando modelo sentence-transformers: {self.huggingface_model}")
            self._hf_model = SentenceTransformer(self.huggingface_model)
        vector = self._hf_model.encode(text[:8000], normalize_embeddings=True)
        return np.array(vector, dtype=np.float32)

    def _embed_ollama(self, text: str) -> np.ndarray:
        """Embedding via Ollama local"""
        import ollama
        response = ollama.embeddings(model=self.ollama_model, prompt=text[:8000])
        return np.array(response["embedding"], dtype=np.float32)

    def _tokenize(self, text: str) -> List[str]:
        """Tokeniza texto para fallback TF-IDF"""
        text = text.lower()
        text = re.sub(r"[^a-zà-ü0-9\s]", " ", text)
        tokens = text.split()
        stopwords = {
            "o", "a", "os", "as", "um", "uma", "de", "do", "da", "dos", "das",
            "e", "ou", "em", "para", "por", "com", "sem", "sobre", "entre",
            "the", "and", "of", "in", "to", "a", "an", "for", "with", "on",
            "is", "are", "was", "were", "be", "been", "being", "have", "has",
            "had", "do", "does", "did", "will", "would", "could", "should"
        }
        return [t for t in tokens if len(t) > 2 and t not in stopwords]

    def _get_token_index(self, token: str, vocab: Dict) -> int:
        """Retorna índice do token no vocabulário"""
        if token not in vocab:
            if len(vocab) < self.embedding_dim:
                vocab[token] = len(vocab)
            else:
                return hash(token) % self.embedding_dim
        return vocab[token]

    def _fallback_embed(self, text: str) -> np.ndarray:
        """Fallback TF-IDF simples para gerar vetor denso"""
        tokens = self._tokenize(text)
        if not tokens:
            return np.zeros(self.embedding_dim, dtype=np.float32)

        vocab = {}
        vector = np.zeros(self.embedding_dim, dtype=np.float32)
        for token in tokens:
            idx = self._get_token_index(token, vocab)
            vector[idx] += 1

        tf = vector / max(len(tokens), 1)
        norm = np.linalg.norm(tf)
        if norm > 0:
            tf = tf / norm
        return tf.astype(np.float32)


def get_embedding_service(
    provider: str = "gemini",
    gemini_api_key: Optional[str] = None
) -> HybridEmbeddingService:
    """Factory padrão"""
    return HybridEmbeddingService(
        provider=provider,
        gemini_api_key=gemini_api_key or os.getenv("GEMINI_API_KEY")
    )

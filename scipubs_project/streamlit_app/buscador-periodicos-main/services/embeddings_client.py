"""
Embeddings Client
Gera embeddings de textos usando Ollama local ou fallback TF-IDF.
"""

import numpy as np
import re
import json
import os
import hashlib
import logging
from typing import List, Optional, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmbeddingsClient:
    """Cliente para geração de embeddings de textos"""

    def __init__(self, model: str = "nomic-embed-text", fallback_dim: int = 512, gemini_api_key: Optional[str] = None):
        """
        Inicializa o cliente de embeddings

        Args:
            model: Modelo Ollama para embeddings (default: nomic-embed-text)
            fallback_dim: Dimensão do vetor no fallback TF-IDF
            gemini_api_key: Chave Gemini para embeddings via API Google
        """
        self.model = model
        self.fallback_dim = fallback_dim
        self.gemini_api_key = gemini_api_key
        self._ollama_available = None
        self._vocab = None
        self._idf = None

    def _check_ollama(self) -> bool:
        """Verifica se Ollama está disponível"""
        if self._ollama_available is None:
            try:
                import ollama
                ollama.list()
                self._ollama_available = True
            except Exception:
                self._ollama_available = False
        return self._ollama_available

    def embed(self, text: str) -> np.ndarray:
        """
        Gera embedding para um texto

        Args:
            text: Texto a ser embeddado

        Returns:
            Array numpy com o vetor de embeddings
        """
        # 1. Tenta Gemini embeddings se houver chave
        if self.gemini_api_key:
            try:
                vector = self._embed_gemini(text)
                if vector is not None:
                    return vector
            except Exception as e:
                logger.warning(f"Erro ao gerar embedding via Gemini: {e}")

        # 2. Tenta Ollama local
        if self._check_ollama():
            try:
                import ollama
                response = ollama.embeddings(model=self.model, prompt=text[:8000])
                vector = response.get("embedding", [])
                if vector:
                    return np.array(vector, dtype=np.float32)
            except Exception as e:
                logger.warning(f"Erro ao gerar embedding via Ollama: {e}. Usando fallback TF-IDF.")

        # 3. Fallback TF-IDF
        return self._fallback_embed(text)

    def _embed_gemini(self, text: str) -> Optional[np.ndarray]:
        """Gera embedding usando API Gemini (embedding-001)"""
        import requests
        url = f"https://generativelanguage.googleapis.com/v1beta/models/embedding-001:embedContent?key={self.gemini_api_key}"
        payload = {
            "content": {"parts": [{"text": text[:8000]}]},
            "taskType": "RETRIEVAL_QUERY"
        }
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        if response.status_code == 200:
            data = response.json()
            values = data.get("embedding", {}).get("values", [])
            if values:
                return np.array(values, dtype=np.float32)
        return None

    def embed_batch(self, texts: List[str]) -> List[np.ndarray]:
        """
        Gera embeddings para uma lista de textos

        Args:
            texts: Lista de textos

        Returns:
            Lista de arrays numpy
        """
        return [self.embed(t) for t in texts]

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

    def _fallback_embed(self, text: str) -> np.ndarray:
        """
        Fallback TF-IDF simples quando Ollama não está disponível.
        Retorna vetor esparso com pesos TF-IDF.
        """
        tokens = self._tokenize(text)
        if not tokens:
            return np.zeros(self.fallback_dim, dtype=np.float32)

        if self._vocab is None:
            self._vocab = {}
            self._idf = np.ones(self.fallback_dim, dtype=np.float32)

        vector = np.zeros(self.fallback_dim, dtype=np.float32)
        for token in tokens:
            idx = self._get_token_index(token)
            vector[idx] += 1

        tf = vector / max(len(tokens), 1)
        vector = tf * self._idf[:self.fallback_dim]

        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        return vector.astype(np.float32)

    def load_pretrained_tfidf(self, vocab: Dict, idf: np.ndarray):
        """Carrega vocabulário e IDF pré-treinados"""
        self._vocab = vocab
        self._idf = idf

    def _get_token_index(self, token: str) -> int:
        """Retorna índice do token no vocabulário (cria se não existir)"""
        if token not in self._vocab:
            if len(self._vocab) < self.fallback_dim:
                self._vocab[token] = len(self._vocab)
            else:
                # Hash para dimensão fixa quando vocabulário enche
                return hash(token) % self.fallback_dim
        return self._vocab[token]

    def fit_tfidf(self, corpus: List[str]):
        """
        Ajusta IDF para fallback TF-IDF

        Args:
            corpus: Lista de documentos para calcular IDF
        """
        if self._check_ollama():
            return  # Não precisa de fallback

        self._vocab = {}
        self._idf = np.zeros(self.fallback_dim, dtype=np.float32)

        doc_count = len(corpus)
        token_doc_count = {}

        for doc in corpus:
            tokens = set(self._tokenize(doc))
            for token in tokens:
                token_doc_count[token] = token_doc_count.get(token, 0) + 1

        for token, count in token_doc_count.items():
            idx = self._get_token_index(token)
            self._idf[idx] = np.log((1 + doc_count) / (1 + count)) + 1

        self._idf[self._idf == 0] = 1.0


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Calcula similaridade de cosseno entre dois vetores"""
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def get_embeddings_client(model: str = "nomic-embed-text", gemini_api_key: Optional[str] = None) -> EmbeddingsClient:
    """Retorna instância do cliente de embeddings"""
    return EmbeddingsClient(model=model, gemini_api_key=gemini_api_key)

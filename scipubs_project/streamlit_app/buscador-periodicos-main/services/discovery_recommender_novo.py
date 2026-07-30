"""
Discovery Recommender (Otimizado)
Motor de recomendação baseado em:
  1. Classificação da área do artigo
  2. Busca vetorial por similaridade de cosseno (com vetores pré-computados)
  3. Probabilidade proxy de publicação
  4. LLM apenas para justificativa (opcional, não bloqueante)
"""

import re
import requests
import os
import pickle
import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Tuple
import logging

from prompts.discovery_prompt import get_justification_prompt
from services.embeddings_client import EmbeddingsClient, cosine_similarity
from services.area_classifier import classify_article_area
from services.cache_manager import get_cache_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DiscoveryRecommender:
    """Motor de recomendação rápido por classificação de área + busca vetorial + proxy"""

    def __init__(
        self,
        df_local: pd.DataFrame,
        api_key_gemini: Optional[str] = None,
        ollama_model: str = "llama3",
        embeddings_model: str = "nomic-embed-text",
        h_index_author: int = 5
    ):
        self.df_local = df_local
        self.api_key_gemini = api_key_gemini
        self.ollama_model = ollama_model
        self.h_index_author = h_index_author
        self.embeddings_client = EmbeddingsClient(model=embeddings_model, gemini_api_key=api_key_gemini)
        self.cache_manager = get_cache_manager()
        self._backend_used = "unknown"
        self.catalog_texts = []
        self.catalog_vectors = []
        self._load_vectors()

    def _load_vectors(self):
        """Carrega vetores pré-computados do catálogo, se disponíveis"""
        cache_path = "data/journal_vectors.pkl"
        if os.path.exists(cache_path):
            try:
                with open(cache_path, "rb") as f:
                    data = pickle.load(f)
                self.catalog_texts = data.get("texts", [])
                self.catalog_vectors = data.get("vectors", [])
                vocab = data.get("vocab")
                idf = data.get("idf")
                if vocab is not None and idf is not None:
                    self.embeddings_client.load_pretrained_tfidf(vocab, idf)
                logger.info(f"Vetores pré-computados carregados: {len(self.catalog_vectors)} revistas")
                return
            except Exception as e:
                logger.warning(f"Erro ao carregar vetores pré-computados: {e}")

        # Fallback: computa vetores em memória (sem salvar)
        logger.info("Computando vetores do catálogo em memória...")
        self._build_catalog_texts()
        self.embeddings_client.fit_tfidf(self.catalog_texts)
        self.catalog_vectors = self.embeddings_client.embed_batch(self.catalog_texts)

    def _build_catalog_texts(self):
        """Constrói textos representativos das revistas"""
        col_titulo = self.df_local.columns[0]
        texts = []
        for _, row in self.df_local.iterrows():
            partes = [str(row[col_titulo])]
            for col in ["Grande Área", "Área do Conhecimento", "Subárea do Conhecimento", "Indexador"]:
                if col in row.index:
                    val = str(row[col])
                    if val and val not in ["-", "nan", "None", ""]:
                        partes.append(val)
            texts.append(" ".join(partes))
        self.catalog_texts = texts

    def get_backend_name(self) -> str:
        return self._backend_used

    def _call_llm_fast(self, prompt: str) -> Optional[str]:
        """Chamada rápida à LLM para justificativa"""
        if self.api_key_gemini:
            try:
                return self._call_gemini(prompt, timeout=10)
            except Exception:
                pass
        try:
            import ollama
            response = ollama.generate(
                model=self.ollama_model,
                prompt=prompt,
                stream=False,
                options={"num_predict": 250, "temperature": 0.7}
            )
            return response.get("response", "")
        except Exception:
            return None

    def _call_gemini(self, prompt: str, timeout: int = 15) -> Optional[str]:
        """Chamada à API Gemini com timeout moderado"""
        modelos = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"]
        for modelo in modelos:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={self.api_key_gemini}"
                response = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]},
                                         headers={"Content-Type": "application/json"}, timeout=timeout)
                if response.status_code == 200:
                    return response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                else:
                    logger.warning(f"Gemini {modelo} retornou {response.status_code}: {response.text[:200]}")
            except Exception as e:
                logger.warning(f"Erro ao chamar Gemini {modelo}: {e}")
                continue
        return None

    def _classificar_artigo(self, titulo: str, resumo: str) -> Dict:
        return classify_article_area(titulo, resumo)

    def _busca_vetorial(self, query_text: str, df_candidatos: pd.DataFrame, top_k: int = 40) -> List[Dict]:
        """Busca vetorial usando vetores pré-carregados"""
        col_titulo = df_candidatos.columns[0]

        # Identifica índices do DataFrame filtrado no DataFrame original
        indices = []
        for idx in df_candidatos.index:
            try:
                pos = self.df_local.index.get_loc(idx)
                if isinstance(pos, slice):
                    pos = pos.start
                indices.append((idx, int(pos)))
            except Exception:
                continue

        query_vector = self.embeddings_client.embed(query_text)

        similarities = []
        for df_idx, vec_idx in indices:
            if vec_idx < len(self.catalog_vectors):
                sim = cosine_similarity(query_vector, self.catalog_vectors[vec_idx])
                similarities.append((df_idx, sim))

        similarities.sort(key=lambda x: x[1], reverse=True)

        results = []
        for df_idx, sim in similarities[:top_k]:
            row = self.df_local.loc[df_idx]
            results.append({
                "nome": str(row[col_titulo]),
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

    def _taxa_aceitacao_historica(self, journal: Dict) -> float:
        quartil = str(journal.get("quartil_jcr", "")).upper()
        sjr_q = str(journal.get("sjr_quartile", "")).upper()
        taxa = 35.0
        if quartil == "Q1" or sjr_q == "Q1":
            taxa = 18.0
        elif quartil == "Q2" or sjr_q == "Q2":
            taxa = 28.0
        elif quartil == "Q3" or sjr_q == "Q3":
            taxa = 38.0
        elif quartil == "Q4" or sjr_q == "Q4":
            taxa = 48.0
        elif quartil in ["-", "", "N/A"] and sjr_q in ["-", "", "N/A"]:
            taxa = 42.0

        indexador = str(journal.get("indexador", "")).lower()
        indexadores_list = [i.strip() for i in indexador.split(",") if i.strip()]
        reconhecidos = ["wos", "scopus", "scielo", "educ@", "doaj"]
        count = sum(1 for idx in indexadores_list if any(r in idx for r in reconhecidos))
        if count >= 3:
            taxa -= 5
        elif count == 0:
            taxa += 5

        return max(5.0, min(taxa, 80.0))

    def _penalidade_incompatibilidade(self, journal: Dict, classificacao: Dict) -> float:
        area_artigo = classificacao.get("grande_area", "").lower()
        area_revista = str(journal.get("grande_area", "")).lower()

        if not area_artigo or not area_revista or area_artigo == area_revista:
            return 1.0

        proximas = {
            "ciências humanas": ["linguística, letras e artes", "ciências sociais aplicadas"],
            "linguística, letras e artes": ["ciências humanas"],
            "ciências sociais aplicadas": ["ciências humanas", "linguística, letras e artes"],
            "ciências da saúde": ["ciências biológicas"],
            "ciências biológicas": ["ciências da saúde", "ciências agrárias"],
            "engenharias": ["ciências exatas e da terra"],
            "ciências exatas e da terra": ["engenharias"]
        }

        for prox in proximas.get(area_artigo, []):
            if prox in area_revista:
                return 0.75

        return 0.45

    def _h_index_revista(self, journal: Dict) -> float:
        h = journal.get("h_index", "-")
        try:
            return float(h) if h not in [None, "-", "N/A", "", "nan"] else 0.0
        except (ValueError, TypeError):
            return 0.0

    def _calcular_probabilidade_proxy(self, journal: Dict, classificacao: Dict) -> float:
        taxa = self._taxa_aceitacao_historica(journal)
        penalidade = self._penalidade_incompatibilidade(journal, classificacao)

        h_revista = self._h_index_revista(journal)
        if h_revista > 0:
            ratio = self.h_index_author / max(h_revista * 0.1, 1.0)
            fator_h = min(1.2, max(0.6, ratio))
        else:
            fator_h = 1.0

        probabilidade = taxa * penalidade * fator_h
        return round(min(probabilidade, 95.0), 1)

    def recommend(
        self,
        titulo: str,
        resumo: str,
        idioma: str = "Português",
        top_n: int = 20,
        use_ollama: bool = False
    ) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """Gera recomendações rapidamente"""
        cache_key = f"rec_v3_{hash(titulo + resumo + str(top_n) + idioma)}"
        cached = self.cache_manager.get(cache_key)
        if cached:
            return cached, None

        query_text = f"{titulo} {resumo}"

        # Etapa 1: Classificar área
        classificacao = self._classificar_artigo(titulo, resumo)
        area_artigo = classificacao.get("grande_area", "")

        # Etapa 2: Filtrar catálogo pela área
        df_candidatos = self.df_local.copy()
        if area_artigo and area_artigo != "Outras / Não Classificado":
            col_area = "Grande Área"
            if col_area in df_candidatos.columns:
                mask = df_candidatos[col_area].astype(str).str.contains(area_artigo, case=False, na=False)
                df_filtrado = df_candidatos[mask]
                if len(df_filtrado) >= 20:
                    df_candidatos = df_filtrado

        # Etapa 3: Busca vetorial -> Top 40
        candidates = self._busca_vetorial(query_text, df_candidatos, top_k=40)
        if not candidates:
            return None, "Nenhuma revista encontrada no catálogo."

        # Etapa 4: Probabilidade proxy
        for j in candidates:
            j["probabilidade_aceitacao"] = self._calcular_probabilidade_proxy(j, classificacao)
            j["classificacao_area"] = classificacao

        # Etapa 5: Ordenar por: aderência desc, probabilidade desc, métricas de impacto desc
        def _parse_num(val):
            try:
                v = float(val)
                if pd.notna(v):
                    return v
            except (ValueError, TypeError):
                pass
            return 0.0

        def _quartil_score(q):
            q = str(q).upper().replace("Q", "").strip()
            try:
                n = int(q)
                return 5 - n  # Q1=4, Q2=3, Q3=2, Q4=1
            except (ValueError, TypeError):
                return 0

        def _score(j):
            return (
                j.get("aderencia", 0),
                j.get("probabilidade_aceitacao", 0),
                _parse_num(j.get("sjr", 0)),
                _parse_num(j.get("jif", 0)),
                _parse_num(j.get("h_index", 0)),
                _quartil_score(j.get("quartil_jcr", "")),
            )

        candidates.sort(key=_score, reverse=True)
        top_journals = candidates[:top_n]

        # Etapa 6: Justificativa (não bloqueante)
        self._backend_used = "vetorial"
        if self.api_key_gemini or self._ollama_available():
            self._backend_used = "gemini" if self.api_key_gemini else "ollama"
            for j in top_journals[:5]:
                try:
                    prompt = get_justification_prompt(titulo, resumo, j, idioma)
                    justificativa = self._call_llm_fast(prompt)
                    if justificativa:
                        j["justificativa"] = justificativa
                except Exception:
                    pass

        for j in top_journals:
            if not j.get("justificativa"):
                j["justificativa"] = self._justificativa_padrao(j, idioma)

        self.cache_manager.set(cache_key, top_journals, ttl=86400)
        return top_journals, None

    def _ollama_available(self) -> bool:
        try:
            import ollama
            ollama.list()
            return True
        except Exception:
            return False

    def _justificativa_padrao(self, journal: Dict, idioma: str) -> str:
        nome = journal.get("nome", "")
        aderencia = journal.get("aderencia", 0)
        probabilidade = journal.get("probabilidade_aceitacao", 0)
        area = journal.get("grande_area", "")

        if idioma == "English":
            return f"{nome} matches your article well. Its editorial scope in {area} shows {aderencia}% thematic adherence, with an estimated {probabilidade}% publication probability."
        elif idioma == "Español":
            return f"{nome} se ajusta bien a su artículo. Su alcance editorial en {area} muestra {aderencia}% de adherencia temática, con probabilidad estimada de publicación del {probabilidade}%."
        return f"{nome} combina bem com seu artigo. Seu escopo editorial em {area} apresenta {aderencia}% de aderência temática, com probabilidade estimada de publicação de {probabilidade}%."

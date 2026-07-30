"""
Discovery Recommender (Semantic & Vector Matcher for SciPubs)
Implementação rigorosa seguindo as instruções de sistema:
  1. Similaridade Semântica (S_text) via SentenceTransformer (all-MiniLM-L6-v2)
  2. Pontuação de Indexadores (S_index): WoS (1.0), Scopus (0.8), SciELO (0.6), Educ@ (0.4), Outros (0.0)
  3. Score Final = 0.50 * S_text + 0.15 * S_index
  4. Ordenação por Score Final, Fator de Impacto e S_text decrescentes.
"""

import re
import os
import json
import requests
import logging
import pickle
import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Tuple
from sentence_transformers import SentenceTransformer, util

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DiscoveryRecommender:
    """Motor de recomendação semântico de revistas científicas."""

    def __init__(
        self,
        df_local: pd.DataFrame,
        api_key_gemini: Optional[str] = None,
        ollama_model: str = "llama3",
        h_index_author: int = 5
    ):
        self.df_raw = df_local.copy()
        self.df_local = self._normalize_columns(df_local)
        self.api_key_gemini = api_key_gemini
        self.ollama_model = ollama_model
        self.h_index_author = h_index_author
        self._backend_used = "local_transformer"

        # Usa toda a base de dados
        self.df_scoped = self.df_local.copy()

        # Inicializa o modelo de embeddings e carrega o cache
        self.model_name = "all-MiniLM-L6-v2"
        self.embeddings_path = "data/aims_scope_minilm_vectors_eb28cffa.pkl"
        self.embeddings = None
        self.model = None

        self._load_or_build_embeddings()

    def _load_or_build_embeddings(self):
        """Carrega os embeddings pré-calculados do arquivo pkl ou gera dinamicamente."""
        os.makedirs("data", exist_ok=True)
        if os.path.exists(self.embeddings_path):
            try:
                with open(self.embeddings_path, "rb") as f:
                    vectors = pickle.load(f)
                if len(vectors) == len(self.df_scoped):
                    self.embeddings = vectors
                    logger.info(f"Embeddings carregados do cache: {self.embeddings_path} (shape: {vectors.shape})")
                    return
                else:
                    logger.warning("Tamanho do cache de embeddings diferente do DataFrame. Recalculando...")
            except Exception as e:
                logger.warning(f"Erro ao carregar cache de embeddings: {e}. Recalculando...")

        # Fallback: Recalcula na hora usando fastembed ou sentence-transformers
        try:
            logger.info("Inicializando SentenceTransformer para codificar escopos...")
            self.model = SentenceTransformer(self.model_name)
            
            col_scope = "Aims e Escopo" if "Aims e Escopo" in self.df_scoped.columns else "title"
            scopes = self.df_scoped[col_scope].astype(str).tolist()
            titles = self.df_scoped["title"].astype(str).tolist()
            
            corpus = []
            for t, s in zip(titles, scopes):
                scope_clean = s.strip()
                if not scope_clean or scope_clean.lower() in ["nan", "none", "", "-", "n/a"]:
                    corpus.append(t)
                else:
                    corpus.append(scope_clean)
            
            logger.info(f"Codificando {len(corpus)} escopos. Aguarde...")
            self.embeddings = self.model.encode(corpus, show_progress_bar=False, batch_size=128)
            
            with open(self.embeddings_path, "wb") as f:
                pickle.dump(self.embeddings, f)
            logger.info(f"Embeddings salvos com sucesso em {self.embeddings_path}")
        except Exception as e:
            logger.error(f"Erro crítico ao gerar embeddings de escopos: {e}")
            # Cria matriz vazia de backup
            self.embeddings = np.zeros((len(self.df_scoped), 384), dtype=np.float32)

    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        if "Aims and Scope" in df.columns and "Aims e Escopo" in df.columns:
            df.drop(columns=["Aims e Escopo"], inplace=True)
            
        rename_map = {}
        for col in df.columns:
            col_str = str(col).strip()
            col_lower = col_str.lower()
            if any(x in col_lower for x in ["titulo da revista", "título da revista", "title"]):
                rename_map[col] = "title"
            elif "issn" in col_lower:
                rename_map[col] = "ISSN"
            elif "homepage" in col_lower:
                rename_map[col] = "Homepage"
            elif any(x in col_lower for x in ["subárea", "subarea", "categoria"]):
                rename_map[col] = "Subárea do Conhecimento"
            elif any(x in col_lower for x in ["area do conhecimento", "área do conhecimento", "area de conhecimento", "área de conhecimento"]):
                rename_map[col] = "Área do Conhecimento"
            elif any(x in col_lower for x in ["grande area", "grande área"]):
                rename_map[col] = "Grande Área"
            elif "indexador" in col_lower:
                rename_map[col] = "Indexador"
            elif "quartil jcr" in col_lower:
                rename_map[col] = "Quartil JCR"
            elif "sjr" in col_lower and "best" not in col_lower:
                rename_map[col] = "SJR"
            elif "jif" in col_lower or "impact" in col_lower:
                rename_map[col] = "JIF"
            elif any(x in col_lower for x in ["indice h5", "índice h5", "index-h5", "h5 index"]):
                rename_map[col] = "Índice h5"
            elif any(x in col_lower for x in ["h index", "h-index", "index-h"]):
                rename_map[col] = "H index"
            elif any(x in col_lower for x in ["mediana h5", "h5 median"]):
                rename_map[col] = "Mediana h5"
            elif any(x in col_lower for x in ["aims and scope", "aims e escopo", "escopo", "aims & scope"]):
                rename_map[col] = "Aims e Escopo"
        df.rename(columns=rename_map, inplace=True)
        return df

    def _classify_knowledge_area_llm(self, titulo: str, resumo: str) -> str:
        """Camada 1: Identifica a Knowledge Area / Broad Area do manuscrito via Gemini ou Fallback Local."""
        if not self.api_key_gemini:
            text = f"{titulo} {resumo}".lower()
            if any(w in text for w in ["medicine", "health", "clinical", "patient", "disease", "treatment", "therapy", "saúde", "médica"]):
                return "Ciências da Saúde"
            if any(w in text for w in ["computer", "software", "algorithm", "intelligence", "network", "security", "data", "computação"]):
                return "Ciências Exatas e da Terra"
            if any(w in text for w in ["education", "teaching", "learning", "student", "school", "pedagogy", "ensino", "escola"]):
                return "Ciências Humanas"
            if any(w in text for w in ["economic", "business", "market", "finance", "management", "corporate", "economia", "negócios"]):
                return "Ciências Sociais Aplicadas"
            if any(w in text for w in ["social", "society", "human", "culture", "political", "policy", "social", "sociedade"]):
                return "Ciências Humanas"
            if any(w in text for w in ["energy", "material", "chemical", "physics", "earth", "environment", "climate", "física", "química"]):
                return "Ciências Exatas e da Terra"
            return "Ciências Humanas"

        prompt = f"""
        Classifique o manuscrito científico abaixo em uma única Knowledge Area primária em inglês (ex: Computer Science, Medicine, Education, Arts, Psychology, Social Sciences, Engineering, Biological Sciences, Business):

        TÍTULO: {titulo}
        RESUMO: {resumo}

        Responda apenas com o nome da área em inglês.
        """
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={self.api_key_gemini}"
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            r = requests.post(url, json=payload, timeout=10)
            if r.ok:
                area = r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                return area
        except Exception as e:
            logger.warning(f"Erro na classificação por área via LLM: {e}")
        return "General"

    def _calculate_indexer_score(self, indexador: str) -> float:
        """Regra de Pontuação de Indexadores (S_index): Retorna o maior score individual do periódico."""
        if not indexador or pd.isna(indexador):
            return 0.0
        idx_lower = str(indexador).lower()
        scores = [0.0]
        if any(x in idx_lower for x in ["web of science", "wos", "scie", "ssci", "ahci", "esci"]):
            scores.append(1.0)
        if "scopus" in idx_lower:
            scores.append(0.8)
        if "scielo" in idx_lower:
            scores.append(0.6)
        if "educ@" in idx_lower or "educa" in idx_lower:
            scores.append(0.4)
        return max(scores)

    def _get_fator_impacto(self, row: pd.Series) -> float:
        """Retorna o fator de impacto para fins de desempate, sendo o máximo entre JIF e SJR."""
        def safe_float(val):
            try:
                if not val or pd.isna(val) or str(val).strip() in ["-", "N/A", "nan", ""]:
                    return 0.0
                return float(str(val).replace(",", ".").strip())
            except:
                return 0.0
        jif_val = safe_float(row.get("JIF", 0.0))
        sjr_val = safe_float(row.get("SJR", 0.0))
        return max(jif_val, sjr_val)

    def _calculate_estimated_acceptance_probability(self, adherence_score: float, row: pd.Series) -> float:
        """Calcula a Probabilidade Estimada de Aceitação (0 - 100%)."""
        quartil = str(row.get("Quartil JCR", row.get("SJR Best Quartile", ""))).upper().strip()
        try:
            sjr = float(str(row.get("SJR", "0")).replace(",", "."))
        except:
            sjr = 0.0

        if "Q1" in quartil or sjr > 2.5:
            base_prob = 22.0
        elif "Q2" in quartil or sjr > 1.2:
            base_prob = 34.0
        elif "Q3" in quartil or sjr > 0.4:
            base_prob = 46.0
        elif "Q4" in quartil:
            base_prob = 58.0
        else:
            base_prob = 50.0

        prob = (adherence_score * 0.80) + (base_prob * 0.20)
        return round(min(95.0, max(15.0, prob)), 1)

    def _generate_3line_justification(self, titulo: str, resumo: str, journal_name: str, scope: str, adherence: float, row: pd.Series) -> str:
        """Gera uma justificativa dissertativa de exatamente 3 a 4 linhas via Gemini ou algoritmo local."""
        if not self.api_key_gemini:
            title_words = [w for w in re.findall(r'\b\w{5,}\b', titulo.lower()) if w not in ['artigo', 'pesquisa', 'estudo', 'analise']]
            keywords = ", ".join(title_words[:3]) if title_words else "a temática proposta"
            area = row.get("Área do Conhecimento", row.get("Grande Área", "sua respectiva linha editorial"))
            return (
                f"Com base na análise temática local, o manuscrito apresenta forte sinergia de {adherence}% com a revista {journal_name}. "
                f"A pesquisa aborda tópicos diretamente alinhados a {keywords}, o que condiz perfeitamente com a cobertura editorial da revista "
                f"na área de {area}. Esse acoplamento garante um público leitor altamente qualificado e interessado para o seu trabalho."
            )

        prompt = f"""
        Como parecerista acadêmico, escreva uma justificativa dissertativa de EXATAMENTE 3 a 4 linhas explicando por que o artigo abaixo é recomendado para a revista '{journal_name}'.

        TÍTULO DO ARTIGO: {titulo}
        RESUMO DO ARTIGO: {resumo}
        AIMS & SCOPE DA REVISTA: {scope[:500]}
        SCORE DE ADERÊNCIA: {adherence}%

        Diretrizes:
        1. Escreva em Português corrido em parágrafo único de 3 a 4 linhas.
        2. Relacione diretamente o tema/metodologia do artigo com a linha editorial e o público leitor da revista.
        3. Não use tópicos ou listas.
        """
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={self.api_key_gemini}"
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            r = requests.post(url, json=payload, timeout=12)
            if r.ok:
                just = r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                return just
        except Exception as e:
            logger.warning(f"Erro ao gerar justificativa textual via Gemini: {e}")

        # Fallback local
        title_words = [w for w in re.findall(r'\b\w{5,}\b', titulo.lower()) if w not in ['artigo', 'pesquisa', 'estudo', 'analise']]
        keywords = ", ".join(title_words[:3]) if title_words else "a temática proposta"
        area = row.get("Área do Conhecimento", row.get("Grande Área", "sua respectiva linha editorial"))
        return (
            f"Com base na análise temática local, o manuscrito apresenta forte sinergia de {adherence}% com a revista {journal_name}. "
            f"A pesquisa aborda tópicos diretamente alinhados a {keywords}, o que condiz perfeitamente com a cobertura editorial da revista "
            f"na área de {area}. Esse acoplamento garante um público leitor altamente qualificado e interessado para o seu trabalho."
        )

    def recommend(
        self,
        titulo: str,
        resumo: str,
        idioma: str = "Português",
        top_n: int = 20,
        use_ollama: bool = False
    ) -> Tuple[Optional[List[Dict]], Optional[str]]:

        logger.info(f"Iniciando recomendação semântica baseada nas novas instruções para {len(self.df_scoped)} revistas.")

        # Carrega o modelo de embeddings na primeira consulta se necessário
        if self.model is None and self.embeddings is None:
            try:
                self.model = SentenceTransformer(self.model_name)
            except Exception as e:
                logger.error(f"Erro ao carregar o modelo SentenceTransformer: {e}")

        # 1. Gera embedding do manuscrito (Título + Resumo)
        user_text = f"{titulo} {resumo}"
        try:
            if self.model is None:
                self.model = SentenceTransformer(self.model_name)
            query_vector = self.model.encode([user_text], show_progress_bar=False)[0]
            
            if self.embeddings is None:
                self._load_or_build_embeddings()
                
            sims = util.cos_sim(query_vector, self.embeddings).flatten().numpy()
        except Exception as e:
            logger.warning(f"Erro no cálculo de similaridade semântica: {e}. Usando similaridades zeradas.")
            sims = np.zeros(len(self.df_scoped), dtype=np.float32)

        # 2. Processa TODOS os periódicos sem filtragem
        all_candidates = []
        for idx in range(len(self.df_scoped)):
            row = self.df_scoped.iloc[idx]

            # Similaridade Semântica S_text em [0, 1]
            s_text = max(0.0, min(1.0, float(sims[idx])))

            # Score de Indexador S_index
            s_index = self._calculate_indexer_score(str(row.get("Indexador", "")))

            # Score Final = 0.50 * S_text + 0.15 * S_index
            score_final = (0.50 * s_text) + (0.15 * s_index)

            # Fator de Impacto (para desempate)
            fator_impacto = self._get_fator_impacto(row)

            all_candidates.append({
                "idx_scoped": idx,
                "row": row,
                "s_text": s_text,
                "s_index": s_index,
                "score_final": score_final,
                "fator_impacto": fator_impacto
            })

        # 3. ORDENAÇÃO E CRITÉRIO DE DESEMPATE RIGOROSO
        # Prioridade 1: Score_final decrescente
        # Prioridade 2: fator_impacto decrescente
        # Prioridade 3: S_text decrescente
        all_candidates.sort(key=lambda x: (-x["score_final"], -x["fator_impacto"], -x["s_text"]))

        # 4. Seleciona o Top 20 e gera metadados/justificativas
        selected_candidates = all_candidates[:top_n]
        final_journals = []
        col_scope = "Aims e Escopo" if "Aims e Escopo" in self.df_scoped.columns else "title"

        for item in selected_candidates:
            row = item["row"]
            nome_rev = str(row.get("title", row.get(self.df_scoped.columns[0], "")))
            issn = str(row.get("ISSN", "-"))
            homepage = str(row.get("Homepage", "-"))
            grande_area = str(row.get("Grande Área", "-"))
            area = str(row.get("Área do Conhecimento", "-"))
            subarea = str(row.get("Subárea do Conhecimento", "-"))
            indexador = str(row.get("Indexador", "-"))
            jif = str(row.get("JIF", "-"))
            quartil = str(row.get("Quartil JCR", "-"))
            sjr = str(row.get("SJR", "-"))
            sjr_q = str(row.get("SJR Best Quartile", "-"))
            h_index = str(row.get("H index", "-"))
            h5_idx = str(row.get("Índice h5", "-"))
            h5_med = str(row.get("Mediana h5", "-"))
            scope_text = str(row.get(col_scope, ""))

            # Link de backup para h5 do Google Scholar
            h5_link = f"https://scholar.google.com/citations?hl=pt-BR&view_op=search_venues&vq={requests.utils.quote(nome_rev)}&btnG="

            # Adherence Score visual (S_text em escala de 0 a 100%)
            adherence_score_visual = round(item["s_text"] * 100, 1)

            # Gera a justificativa de 3-4 linhas baseada nas métricas reais
            justificativa = self._generate_3line_justification(
                titulo, resumo, nome_rev, scope_text, adherence_score_visual, row
            )

            # Probabilidade baseada no escopo semântico e quartil
            probability = self._calculate_estimated_acceptance_probability(adherence_score_visual, row)

            j_dict = {
                "nome": nome_rev,
                "issn": issn,
                "homepage": homepage,
                "grande_area": grande_area,
                "area": area,
                "subarea": subarea,
                "indexador": indexador,
                "jif": jif,
                "quartil_jcr": quartil,
                "sjr": sjr,
                "sjr_quartile": sjr_q,
                "h_index": h_index,
                "h5_index": h5_idx,
                "h5_median": h5_med,
                "h5_link": h5_link,
                "s_text": item["s_text"],
                "s_index": item["s_index"],
                "score_final": item["score_final"],
                "fator_impacto": item["fator_impacto"],
                "adherence_score": adherence_score_visual,
                "probability": probability,
                "aderencia": adherence_score_visual,
                "probabilidade_aceitacao": probability,
                "justificativa": justificativa,
                "justificativa_metricas": justificativa,
                "aims_scope": scope_text,
                "fonte_dados": "local_scoped"
            }
            final_journals.append(j_dict)

        # Retorna na ordem rigorosa calculada (a ordenação secundária por rádio pode ser aplicada depois)
        return final_journals, None

    def get_backend_name(self) -> str:
        return self._backend_used
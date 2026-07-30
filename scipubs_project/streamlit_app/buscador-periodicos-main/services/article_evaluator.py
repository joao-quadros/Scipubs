"""
Article Evaluator
Calcula índices de avaliação do artigo (aderência, probabilidade de aceitação)
"""

import pandas as pd
from typing import Dict, Optional, List
import logging

from prompts.discovery_prompt import get_classification_prompt
from utils.fuzzy_matcher import find_journal_in_dataframe

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ArticleEvaluator:
    """Avaliador de artigo com múltiplos índices"""
    
    def __init__(self, df_local: pd.DataFrame, ollama_model: str = "llama3"):
        """
        Inicializa o avaliador
        
        Args:
            df_local: DataFrame com base local de revistas
            ollama_model: Modelo Ollama a usar
        """
        self.df_local = df_local
        self.ollama_model = ollama_model
    
    def _call_ollama(self, prompt: str) -> Optional[str]:
        """
        Faz chamada ao Ollama
        
        Args:
            prompt: Prompt para enviar
            
        Returns:
            Resposta do modelo ou None
        """
        try:
            import ollama
            response = ollama.generate(
                model=self.ollama_model,
                prompt=prompt,
                stream=False
            )
            return response['response']
        except ImportError:
            logger.error("Ollama não está instalado")
            return None
        except Exception as e:
            logger.error(f"Erro ao chamar Ollama: {e}")
            return None
    
    def classify_article_area(
        self,
        titulo: str,
        resumo: str,
        idioma: str = "Português"
    ) -> Optional[Dict]:
        """
        Classifica o artigo nas áreas CAPES
        
        Args:
            titulo: Título do artigo
            resumo: Resumo do artigo
            idioma: Idioma do prompt
            
        Returns:
            Dicionário com classificação ou None
        """
        prompt = get_classification_prompt(titulo, resumo, idioma)
        
        try:
            import json
            response = self._call_ollama(prompt)
            
            if response:
                # Remove markdown se presente
                response = response.strip()
                if response.startswith("```"):
                    response = response.split("```")[1]
                    if response.startswith("json"):
                        response = response[4:]
                
                classification = json.loads(response.strip())
                return classification
        except Exception as e:
            logger.error(f"Erro ao classificar artigo: {e}")
        
        return None
    
    def calculate_area_adherence(
        self,
        article_area: str,
        journal_area: str
    ) -> float:
        """
        Calcula aderência da área do artigo com a área da revista
        
        Args:
            article_area: Área do artigo
            journal_area: Área da revista
            
        Returns:
            Score de aderência (0-100)
        """
        if not article_area or not journal_area:
            return 50.0
        
        article_area = str(article_area).lower().strip()
        journal_area = str(journal_area).lower().strip()
        
        # Match exato
        if article_area == journal_area:
            return 100.0
        
        # Match parcial (contém)
        if article_area in journal_area or journal_area in article_area:
            return 75.0
        
        # Áreas próximas (lista de sinônimos)
        similar_areas = {
            "ciência da computação": ["computação", "informática", "sistemas de informação"],
            "engenharia": ["engenharias", "engenharia de"],
            "saúde": ["ciências da saúde", "medicina", "enfermagem"],
            "educação": ["educação", "ensino", "pedagogia"]
        }
        
        for key, synonyms in similar_areas.items():
            if article_area in synonyms and journal_area in synonyms:
                return 60.0
        
        return 30.0
    
    def calculate_acceptance_probability(
        self,
        journal: Dict,
        article_adherence: float,
        similar_articles_count: int = 0
    ) -> Dict:
        """
        Calcula probabilidade proxy de aceitação baseada em múltiplos critérios.

        Fórmula ponderada:
        - Aderência ao escopo (35%): prioridade absoluta do alinhamento temático.
        - Existência/quantidade de artigos similares (25%): histórico de publicações
          similares indica que a revista já aceitou trabalhos na linha do usuário.
        - Métricas da revista (25%): prestígio, quartil JCR/SJR, h-index e indexadores.
        - Aderência linguística/formato (15%): compatibilidade entre idioma do artigo
          e idioma predominante da revista.
        """
        score = 0.0
        detalhes = []

        # 1. Aderência ao escopo (35%)
        score += article_adherence * 0.35
        detalhes.append(f"aderência ao escopo ({article_adherence:.0f}%)")

        # 2. Artigos similares publicados (25%)
        similar_score = min(similar_articles_count * 20, 100)
        score += similar_score * 0.25
        if similar_articles_count > 0:
            detalhes.append(f"{similar_articles_count} artigo(s) similar(es) publicado(s) na revista")
        else:
            detalhes.append("nenhum artigo similar encontrado na revista")

        # 3. Métricas da revista (25%)
        quartil = journal.get("quartil_jcr", "")
        sjr_quartile = journal.get("sjr_quartile", "")
        h_index = journal.get("h_index")
        indexador = str(journal.get("indexador", "")).lower()

        try:
            h_index_val = float(h_index) if h_index not in [None, "-", "N/A", "", "nan"] else 0
        except (ValueError, TypeError):
            h_index_val = 0

        # Prestígio convertido em oportunidade: revistas com maior visibilidade
        # aumentam a chance de encontrar leitores e revisores adequados.
        prestige_score = 80.0
        if quartil == "Q1":
            prestige_score = 85.0
        elif quartil == "Q2":
            prestige_score = 88.0
        elif quartil == "Q3":
            prestige_score = 90.0
        elif quartil == "Q4":
            prestige_score = 92.0
        elif sjr_quartile == "Q1":
            prestige_score = 86.0
        elif sjr_quartile == "Q2":
            prestige_score = 88.0
        elif sjr_quartile == "Q3":
            prestige_score = 90.0
        elif sjr_quartile == "Q4":
            prestige_score = 92.0
        elif h_index_val > 0:
            if h_index_val >= 100:
                prestige_score = 86.0
            elif h_index_val >= 50:
                prestige_score = 88.0
            elif h_index_val >= 20:
                prestige_score = 90.0
            else:
                prestige_score = 92.0

        # Bônus por múltiplos indexadores reconhecidos
        indexadores_list = [i.strip() for i in indexador.split(",") if i.strip()]
        reconhecidos = ["wos", "scopus", "scielo", "educ@", "doaj"]
        count_reconhecidos = sum(1 for idx in indexadores_list if any(r in idx for r in reconhecidos))
        if count_reconhecidos >= 2:
            prestige_score = min(prestige_score + 5, 100)

        score += prestige_score * 0.25
        detalhes.append(f"prestígio editorial ({prestige_score:.0f}%)")

        # 4. Aderência linguística (15%)
        idioma_artigo = str(journal.get("idioma", "")).upper()
        idioma_revista = str(journal.get("idioma", "")).upper()
        if idioma_artigo and idioma_revista:
            if idioma_artigo == idioma_revista:
                lang_score = 100.0
            elif idioma_artigo in ["PT", "ES"] and idioma_revista in ["PT", "ES"]:
                lang_score = 85.0
            elif idioma_artigo == "EN" and idioma_revista == "EN":
                lang_score = 100.0
            elif idioma_artigo in ["PT", "ES"] and idioma_revista == "EN":
                lang_score = 75.0
            else:
                lang_score = 60.0
        else:
            lang_score = 80.0
        score += lang_score * 0.15
        detalhes.append(f"compatibilidade de idioma ({lang_score:.0f}%)")

        # Cap em 100
        probability = min(score, 100.0)

        # Determina nível de confiança
        if probability >= 75:
            confianca = "Alta"
        elif probability >= 50:
            confianca = "Média"
        else:
            confianca = "Baixa"

        return {
            "probabilidade": round(probability, 1),
            "confianca": confianca,
            "metodo": "Estimativa baseada em aderência temática, artigos similares publicados, métricas da revista e compatibilidade de idioma",
            "detalhes": detalhes
        }
    
    def evaluate_article_for_journal(
        self,
        titulo: str,
        resumo: str,
        journal: Dict,
        similar_articles_count: int = 0,
        idioma: str = "Português"
    ) -> Dict:
        """
        Avalia artigo para uma revista específica
        
        Args:
            titulo: Título do artigo
            resumo: Resumo do artigo
            journal: Dados da revista
            similar_articles_count: Número de artigos similares
            idioma: Idioma
            
        Returns:
            Dicionário com todos os índices
        """
        # 1. Aderência ao escopo (já vem da IA)
        aderencia_escopo = journal.get("aderencia", 0)
        
        # 2. Classifica área do artigo
        classification = self.classify_article_area(titulo, resumo, idioma)
        
        if classification:
            article_area = classification.get("area", "")
            article_grande_area = classification.get("grande_area", "")
            classification_confidence = classification.get("confianca", 0)
        else:
            article_area = "-"
            article_grande_area = "-"
            classification_confidence = 0
        
        # 3. Aderência à área
        journal_area = journal.get("area", "-")
        aderencia_area = self.calculate_area_adherence(article_area, journal_area)
        
        # 4. Probabilidade de aceitação
        acceptance = self.calculate_acceptance_probability(
            journal,
            aderencia_escopo,
            similar_articles_count
        )

        # 5. Gera justificativa dissertativa das métricas
        justificativa_metricas = self._gerar_justificativa_metricas(
            journal, aderencia_escopo, acceptance, similar_articles_count, idioma
        )

        return {
            "aderencia_escopo": aderencia_escopo,
            "aderencia_area": round(aderencia_area, 1),
            "probabilidade_aceitacao": acceptance["probabilidade"],
            "probabilidade_confianca": acceptance["confianca"],
            "probabilidade_metodo": acceptance["metodo"],
            "artigo_area": article_area,
            "artigo_grande_area": article_grande_area,
            "classificacao_confianca": classification_confidence,
            "justificativa_metricas": justificativa_metricas
        }

    def evaluate_journal_with_classification(
        self,
        journal: Dict,
        classification: Optional[Dict],
        similar_articles_count: int = 0
    ) -> Dict:
        """
        Avalia revista usando classificação CAPES já calculada (sem nova chamada IA).
        """
        aderencia_escopo = journal.get("aderencia", 0)

        if classification:
            article_area = classification.get("area", "")
            article_grande_area = classification.get("grande_area", "")
            classification_confidence = classification.get("confianca", 0)
        else:
            article_area = "-"
            article_grande_area = "-"
            classification_confidence = 0

        journal_area = journal.get("area", "-")
        aderencia_area = self.calculate_area_adherence(article_area, journal_area)

        acceptance = self.calculate_acceptance_probability(
            journal,
            aderencia_escopo,
            similar_articles_count
        )

        return {
            "aderencia_escopo": aderencia_escopo,
            "aderencia_area": round(aderencia_area, 1),
            "probabilidade_aceitacao": acceptance["probabilidade"],
            "probabilidade_confianca": acceptance["confianca"],
            "probabilidade_metodo": acceptance["metodo"],
            "artigo_area": article_area,
            "artigo_grande_area": article_grande_area,
            "classificacao_confianca": classification_confidence,
            "justificativa_metricas": self._gerar_justificativa_metricas(
                journal, aderencia_escopo, acceptance, similar_articles_count, "Português"
            )
        }

    def _gerar_justificativa_metricas(
        self,
        journal: Dict,
        aderencia_escopo: float,
        acceptance: Dict,
        similar_articles_count: int,
        idioma: str = "Português"
    ) -> str:
        """
        Gera texto dissertativo (até 4 linhas) explicando as métricas da revista.
        """
        nome = journal.get("nome", "esta revista")
        quartil = journal.get("quartil_jcr", "-")
        sjr = journal.get("sjr", "-")
        h_index = journal.get("h_index", "-")

        if idioma == "English":
            txt = (
                f"**{nome}** was recommended because the title and abstract show a thematic fit of "
                f"**{aderencia_escopo:.0f}%** with the journal's editorial scope. "
            )
            if similar_articles_count > 0:
                txt += (
                    f"The journal has already published **{similar_articles_count} similar article(s)**, "
                    f"which reinforces the suitability of the submission. "
                )
            else:
                txt += "No similar published articles were found in this journal, so fit relies primarily on semantic scope. "
            txt += (
                f"Considering the journal metrics (JCR quartile {quartil}, SJR {sjr}, h-index {h_index}) "
                f"and the historical editorial profile, the estimated acceptance probability is **{acceptance['probabilidade']:.0f}%**."
            )
        elif idioma == "Español":
            txt = (
                f"**{nome}** fue recomendada porque el título y el resumen muestran una adecuación temática de "
                f"**{aderencia_escopo:.0f}%** con el alcance editorial de la revista. "
            )
            if similar_articles_count > 0:
                txt += (
                    f"La revista ya ha publicado **{similar_articles_count} artículo(s) similar(es)**, "
                    f"lo que refuerza la pertinencia de la propuesta. "
                )
            else:
                txt += "No se encontraron artículos similares publicados en esta revista, por lo que la adecuación se basa principalmente en el alcance semántico. "
            txt += (
                f"Considerando las métricas de la revista (cuartil JCR {quartil}, SJR {sjr}, índice h {h_index}) "
                f"y el perfil editorial histórico, la probabilidad estimada de aceptación es **{acceptance['probabilidade']:.0f}%**."
            )
        else:
            txt = (
                f"**{nome}** foi recomendada porque o título e o resumo apresentam **{aderencia_escopo:.0f}%** "
                f"de aderência ao escopo editorial da revista. "
            )
            if similar_articles_count > 0:
                txt += (
                    f"A revista já publicou **{similar_articles_count} artigo(s) similar(es)**, "
                    f"o que reforça a pertinência da proposta. "
                )
            else:
                txt += "Não foram encontrados artigos similares publicados nesta revista, portanto a aderência se apoia principalmente no escopo semântico. "
            txt += (
                f"Considerando as métricas da revista (quartil JCR {quartil}, SJR {sjr}, h-index {h_index}) "
                f"e o perfil editorial histórico, a probabilidade estimada de aceitação é **{acceptance['probabilidade']:.0f}%**."
            )

        return txt


def get_article_evaluator(df_local: pd.DataFrame, ollama_model: str = "llama3") -> ArticleEvaluator:
    """
    Retorna instância do ArticleEvaluator
    
    Args:
        df_local: DataFrame local
        ollama_model: Modelo Ollama
        
    Returns:
        Instância de ArticleEvaluator
    """
    return ArticleEvaluator(df_local, ollama_model)

"""
Area Classifier
Classifica o artigo na Grande Área do Conhecimento com base em palavras-chave.
"""

import re
import unicodedata
from typing import Dict, Optional


# Mapeamento de grandes áreas e palavras indicadoras
AREA_KEYWORDS = {
    "Ciências Humanas": [
        "educação", "ensino", "pedagogia", "didática", "escola", "professor", "aluno", "aprendizagem",
        "currículo", "avaliação", "formação", "docente", "sala de aula", "prática pedagógica",
        "filosofia", "história", "sociologia", "antropologia", "linguística", "literatura", "arte",
        "música", "educação musical", "humanas", "humanidades", "ensino superior", "pós-graduação",
        "pesquisa qualitativa", "etnografia", "discurso", "identidade", "cultura", "sociedade"
    ],
    "Ciências Sociais Aplicadas": [
        "administração", "economia", "contabilidade", "marketing", "finanças", "gestão",
        "direito", "ciências sociais aplicadas", "comunicação", "jornalismo", "publicidade",
        "turismo", "serviço social", "biblioteconomia", "arquitetura", "urbanismo", "planejamento"
    ],
    "Ciências Exatas e da Terra": [
        "computação", "computador", "informática", "sistemas", "inteligência artificial",
        "machine learning", "deep learning", "algoritmo", "matemática", "física", "química",
        "estatística", "probabilidade", "modelagem", "simulação", "dados", "data science",
        "astronomia", "geofísica", "oceanografia", "meteorologia"
    ],
    "Ciências Biológicas": [
        "biologia", "ecologia", "genética", "microbiologia", "zoologia", "botânica", "biotecnologia",
        "bioquímica", "fisiologia", "anatomia", "biologia molecular", "biodiversidade", "conservação"
    ],
    "Ciências da Saúde": [
        "saúde", "medicina", "enfermagem", "odontologia", "farmácia", "fisioterapia",
        "nutrição", "psicologia", "saúde pública", "epidemiologia", "doença", "paciente",
        "clínica", "hospital", "tratamento", "diagnóstico", "terapia", "intervenção"
    ],
    "Ciências Agrárias": [
        "agronomia", "veterinária", "zootecnia", "floresta", "solo", "agricultura",
        "pecuária", "horticultura", "agronegócio", "fitossanidade", "silvicultura"
    ],
    "Engenharias": [
        "engenharia", "engenharia civil", "engenharia elétrica", "engenharia mecânica",
        "engenharia química", "engenharia de produção", "materiais", "construção",
        "energia", "automação", "robótica", "manufatura", "processos"
    ],
    "Linguística, Letras e Artes": [
        "linguagem", "linguística", "letras", "literatura", "tradução", "semiótica",
        "arte", "música", "teatro", "dança", "cinema", "filologia", "fonética"
    ]
}


def normalize_text(text: str) -> str:
    """Normaliza texto para comparação"""
    text = text.lower()
    text = ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return text


def classify_article_area(titulo: str, resumo: str) -> Dict:
    """
    Classifica o artigo em uma Grande Área do Conhecimento.

    Args:
        titulo: Título do artigo
        resumo: Resumo do artigo

    Returns:
        Dicionário com grande_area, area, subarea e confiança
    """
    texto = normalize_text(f"{titulo} {resumo}")

    scores = {}
    for area, keywords in AREA_KEYWORDS.items():
        score = 0
        for kw in keywords:
            if kw in texto:
                # Palavras do título têm peso maior
                if kw in normalize_text(titulo):
                    score += 3
                else:
                    score += 1
        scores[area] = score

    if not scores or max(scores.values()) == 0:
        return {
            "grande_area": "Outras / Não Classificado",
            "area": "Não Classificado",
            "subarea": "Não Classificado",
            "confianca": 0.0
        }

    best_area = max(scores, key=scores.get)
    best_score = scores[best_area]
    total_score = sum(scores.values())
    confianca = round(best_score / total_score, 2) if total_score > 0 else 0.0

    return {
        "grande_area": best_area,
        "area": best_area,
        "subarea": inferir_subarea(texto, best_area),
        "confianca": confianca
    }


def inferir_subarea(texto: str, grande_area: str) -> str:
    """Infere subárea mais provável dentro da grande área"""
    subareas = {
        "Ciências Humanas": {
            "Educação": ["educação", "ensino", "pedagogia", "didática", "escola", "professor", "aluno", "aprendizagem", "currículo"],
            "Música": ["música", "educação musical", "musical", "canto", "instrumento"],
            "Filosofia": ["filosofia", "ética", "epistemologia", "ontologia"],
            "História": ["história", "memória", "patrimônio"],
            "Sociologia": ["sociologia", "sociedade", "social"],
            "Antropologia": ["antropologia", "etnografia", "cultura"],
            "Linguística": ["linguagem", "discurso", "linguística"]
        },
        "Ciências Exatas e da Terra": {
            "Ciência da Computação": ["computação", "computador", "algoritmo", "inteligência artificial", "machine learning", "sistemas"],
            "Matemática": ["matemática", "estatística", "probabilidade", "modelagem"],
            "Física": ["física", "mecânica", "quântica"],
            "Química": ["química", "molécula", "reação"]
        },
        "Ciências da Saúde": {
            "Medicina": ["medicina", "clínica", "hospital", "doença", "diagnóstico"],
            "Enfermagem": ["enfermagem", "cuidado", "enfermeiro"],
            "Psicologia": ["psicologia", "saúde mental", "comportamento"],
            "Saúde Coletiva": ["saúde pública", "epidemiologia", "coletiva"]
        }
    }

    subs = subareas.get(grande_area, {})
    if not subs:
        return grande_area

    best_sub = "Geral"
    best_score = 0
    for sub, keywords in subs.items():
        score = sum(1 for kw in keywords if kw in texto)
        if score > best_score:
            best_score = score
            best_sub = sub

    return best_sub

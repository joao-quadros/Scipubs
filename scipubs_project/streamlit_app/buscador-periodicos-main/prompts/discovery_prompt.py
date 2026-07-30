"""
Discovery-First Prompt
Prompt otimizado para descoberta de revistas via IA generativa
"""

from typing import Dict


def get_discovery_prompt(
    titulo: str,
    resumo: str,
    lista_periodicos: list = None,
    top_n: int = 20,
    idioma: str = "Português"
) -> str:
    """
    Retorna prompt Discovery-First otimizado

    Args:
        titulo: Título do artigo
        resumo: Resumo do artigo
        lista_periodicos: Lista de candidatos do catálogo local
        top_n: Número de recomendações esperadas
        idioma: Idioma do prompt (Português, English, Español)

    Returns:
        String com o prompt
    """
    base_periodicos = ""
    if lista_periodicos:
        # Limita o contexto para não exceder tokens
        amostra = lista_periodicos[:40]
        linhas = []
        for p in amostra:
            linha = f"- {p.get(list(p.keys())[0], '')}"
            for k, v in p.items():
                if k not in [list(p.keys())[0], "SJR"] and v and str(v) != "-":
                    linha += f" | {k}: {v}"
            linhas.append(linha)
        base_periodicos = "\n".join(linhas)

    if idioma == "Português":
        return f"""Você é um consultor sênior de publicações científicas.
Analise o artigo abaixo e recomende EXATAMENTE {top_n} revistas do catálogo fornecido que tenham o MAIOR alinhamento temático com o artigo.

TÍTULO DO ARTIGO:
{titulo}

RESUMO:
{resumo}

CATÁLOGO DE PERIÓDICOS DISPONÍVEIS (escolha apenas desta lista):
{base_periodicos}

REGRAS OBRIGATÓRIAS:
1. Aderência temática é a PRIORIDADE ABSOLUTA. Não recomende revistas fora da área do artigo.
2. Escolha APENAS revistas que constam no catálogo acima.
3. Diversifique níveis de prestígio (Q1, Q2, Q3, Q4, sem quartil).
4. Considere idioma do artigo e da revista.
5. Aderência de 0 a 100: use de forma realista, com base no escopo editorial.

RESPONDA APENAS com JSON válido (sem markdown), exatamente neste formato:
[
  {{
    "revista_nome": "Nome exato da revista conforme catálogo",
    "aderencia": 85,
    "idioma": "PT",
    "justificativa": "Breve explicação da adequação temática em 2-3 frases"
  }}
]"""

    elif idioma == "English":
        return f"""You are a senior scientific publication advisor.
Analyze the article below and recommend EXACTLY {top_n} journals from the provided catalog that have the GREATEST thematic alignment with the article.

ARTICLE TITLE:
{titulo}

ABSTRACT:
{resumo}

AVAILABLE JOURNAL CATALOG (choose only from this list):
{base_periodicos}

MANDATORY RULES:
1. Thematic adherence is the ABSOLUTE PRIORITY. Do not recommend journals outside the article's field.
2. Choose ONLY journals listed in the catalog above.
3. Diversify prestige levels (Q1, Q2, Q3, Q4, unranked).
4. Consider article and journal language.
5. Adherence 0-100: use realistically based on editorial scope.

RESPOND ONLY with valid JSON (no markdown), exactly in this format:
[
  {{
    "journal_name": "Exact journal name as in catalog",
    "adherence": 85,
    "language": "EN",
    "justification": "Brief explanation of thematic fit in 2-3 sentences"
  }}
]"""

    else:  # Español
        return f"""Usted es un asesor sénior en publicaciones científicas.
Analice el artículo a continuación y recomiende EXACTAMENTE {top_n} revistas del catálogo proporcionado que tengan el MAYOR alineamiento temático con el artículo.

TÍTULO DEL ARTÍCULO:
{titulo}

RESUMEN:
{resumo}

CATÁLOGO DE REVISTAS DISPONIBLES (elija solo de esta lista):
{base_periodicos}

REGLAS OBLIGATORIAS:
1. La adhesión temática es la PRIORIDAD ABSOLUTA. No recomiende revistas fuera del área del artículo.
2. Elija SOLO revistas que aparecen en el catálogo anterior.
3. Diversifique niveles de prestigio (Q1, Q2, Q3, Q4, sin clasificar).
4. Considere el idioma del artículo y de la revista.
5. Adherencia de 0 a 100: use de forma realista según el alcance editorial.

RESPONDA SOLO con JSON válido (sin markdown), exactamente en este formato:
[
  {{
    "revista_nombre": "Nombre exacto de la revista según el catálogo",
    "adherencia": 85,
    "idioma": "ES",
    "justificacion": "Breve explicación de la adecuación temática en 2-3 frases"
  }}
]"""


def get_justification_prompt(
    titulo: str,
    resumo: str,
    revista: Dict,
    idioma: str = "Português"
) -> str:
    """
    Retorna prompt para LLM gerar justificativa qualitativa de um match.
    A LLM não escolhe a revista; apenas redige a explicação.
    """
    nome = revista.get("nome", "")
    aderencia = revista.get("aderencia", 0)
    probabilidade = revista.get("probabilidade_aceitacao", 0)
    quartil = revista.get("quartil_jcr", "-")
    indexador = revista.get("indexador", "-")

    if idioma == "Português":
        return f"""Você é um consultor sênior de publicações científicas.

TÍTULO DO ARTIGO:
{titulo}

RESUMO:
{resumo}

REVISTA RECOMENDADA: {nome}
- Aderência ao escopo calculada: {aderencia}%
- Probabilidade proxy de aceitação: {probabilidade}%
- Quartil JCR: {quartil}
- Indexadores: {indexador}

ESCREVA APENAS uma justificativa de 2 a 3 linhas, em tom profissional e encorajador, explicando por que esta revista é adequada para o artigo. Não use listas, tabelas ou JSON. Texto corrido apenas."""

    elif idioma == "English":
        return f"""You are a senior scientific publication advisor.

ARTICLE TITLE:
{titulo}

ABSTRACT:
{resumo}

RECOMMENDED JOURNAL: {nome}
- Calculated scope adherence: {aderencia}%
- Proxy acceptance probability: {probabilidade}%
- JCR Quartile: {quartil}
- Indexers: {indexador}

WRITE ONLY a 2-3 sentence justification, in a professional and encouraging tone, explaining why this journal is suitable for the article. Do not use lists, tables, or JSON. Plain text only."""

    else:  # Español
        return f"""Usted es un asesor sénior en publicaciones científicas.

TÍTULO DEL ARTÍCULO:
{titulo}

RESUMEN:
{resumo}

REVISTA RECOMENDADA: {nome}
- Adecuación al alcance calculada: {aderencia}%
- Probabilidad proxy de aceptación: {probabilidade}%
- Cuartil JCR: {quartil}
- Indexadores: {indexador}

ESCRIBA SOLO una justificación de 2 a 3 líneas, en tono profesional y alentador, explicando por qué esta revista es adecuada para el artículo. No use listas, tablas ni JSON. Solo texto corrido."""


def get_classification_prompt(titulo: str, resumo: str, idioma: str = "Português") -> str:
    """
    Retorna prompt para classificação CAPES do artigo
    """
    if idioma == "Português":
        return f"""Classifique este artigo nas áreas do CNPq/CAPES:

TÍTULO: {titulo}
RESUMO: {resumo}

RESPONDA apenas com JSON válido:
{{
    "grande_area": "Ex: Ciências Exatas e da Terra",
    "area": "Ex: Ciência da Computação",
    "subarea": "Ex: Sistemas de Computação",
    "confianca": 0.92
}}"""

    elif idioma == "English":
        return f"""Classify this article in CNPq/CAPES areas:

TITLE: {titulo}
ABSTRACT: {resumo}

RESPOND only with valid JSON:
{{
    "grande_area": "Ex: Exact and Earth Sciences",
    "area": "Ex: Computer Science",
    "subarea": "Ex: Computer Systems",
    "confianca": 0.92
}}"""

    else:  # Español
        return f"""Clasifique este artículo en las áreas del CNPq/CAPES:

TÍTULO: {titulo}
RESUMEN: {resumo}

RESPONDA solo con JSON válido:
{{
    "grande_area": "Ex: Ciencias Exactas y de la Tierra",
    "area": "Ex: Ciencia de la Computación",
    "subarea": "Ex: Sistemas de Computación",
    "confianca": 0.92
}}"""

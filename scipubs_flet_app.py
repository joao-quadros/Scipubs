import flet as ft
import pandas as pd
import numpy as np
import os
import time
import pickle
import functools
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

HAS_SENTENCE_TRANSFORMERS = False
SentenceTransformer = None
try:
    import sentence_transformers
    from sentence_transformers import SentenceTransformer as ST
    SentenceTransformer = ST
    HAS_SENTENCE_TRANSFORMERS = True
except BaseException:
    SentenceTransformer = None
    HAS_SENTENCE_TRANSFORMERS = False

os.environ["OPENBLAS_NUM_THREADS"] = "1"

import re
import urllib.parse
import webbrowser
import unicodedata
import logging

logging.getLogger("flet_web").setLevel(logging.WARNING)
logging.getLogger("uvicorn").setLevel(logging.WARNING)

# ==========================================
# 🎨 PALETA DE CORES EXATA DO SCIPUBS
# ==========================================
SIDEBAR_BG = "#F8F6F0"       # Fundo claro da barra lateral (Beige)
MAIN_BG = "#080D1A"          # Fundo escuro da área principal (Deep Navy/Black)
CARD_BG = "#0F172A"          # Cartões escuros principais
INPUT_BG = "#1E293B"         # Fundo de campos de texto
HERO_BLUE = "#040A1A"        # Fundo do Banner Principal (Deep Navy)
ACCENT_RED = "#FF3B30"       # Vermelho oficial SciPubs
CORAL_RED = "#FF3B30"
ACCENT_YELLOW = "#FFCC00"    # Amarelo oficial SciPubs
GOLD_YELLOW = "#FFCC00"
ACCENT_GREEN = "#059669"     # Verde Recomendador
EMERALD_GREEN = "#059669"
ACCENT_BLUE = "#2563EB"      # Azul Royal Buscador
ROYAL_BLUE = "#2563EB"
TEXT_DARK = "#0F172A"        # Texto para fundos claros
TEXT_MUTED = "#94A3B8"       # Texto secundário
BORDER_DARK = "#1E293B"

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
STREAMLIT_DIR = os.path.join(BASE_DIR, "scipubs_project", "streamlit_app", "buscador-periodicos-main")

DADOS_CSV_PATH = os.path.join(STREAMLIT_DIR, "dados.csv")
if not os.path.exists(DADOS_CSV_PATH):
    DADOS_CSV_PATH = os.path.join(BASE_DIR, "dados.csv")

CACHE_PATH = os.path.join(STREAMLIT_DIR, "data", "aims_scope_minilm_vectors.pkl")
if not os.path.exists(CACHE_PATH):
    CACHE_PATH = os.path.join(BASE_DIR, "data", "aims_scope_minilm_vectors.pkl")

ICONS_DIR = os.path.join(BASE_DIR, "icons")
os.makedirs(ICONS_DIR, exist_ok=True)

def get_image_src(nome_arquivo):
    if not nome_arquivo:
        return None
    p = os.path.join(ICONS_DIR, nome_arquivo)
    if os.path.exists(p):
        return nome_arquivo
    return "logo.png"

def get_banner_src(idioma="English"):
    if idioma == "English":
        fname = "banner_en.png"
    elif idioma == "Español":
        fname = "banner_es.png"
    else:
        fname = "banner_pt.png"
    return get_image_src(fname)

REGRAS_ORTOGRAFIA = [
    (r'\bEducacao\b', 'Educação'),
    (r'\beducacao\b', 'educação'),
    (r'\bMusica\b', 'Música'),
    (r'\bmusica\b', 'música'),
    (r'\bSaude\b', 'Saúde'),
    (r'\bsaude\b', 'saúde'),
    (r'\bGestao\b', 'Gestão'),
    (r'\bgestao\b', 'gestão'),
    (r'\bProducao\b', 'Produção'),
    (r'\bproducao\b', 'produção'),
    (r'\bAvaliacao\b', 'Avaliação'),
    (r'\bavaliacao\b', 'avaliação'),
    (r'\bEletronica\b', 'Eletrônica'),
    (r'\beletronica\b', 'eletrônica'),
    (r'\bCien\.\b', 'Ciên.'),
    (r'\bCiencia\b', 'Ciência'),
    (r'\bciencia\b', 'ciência'),
    (r'\bCiencias\b', 'Ciências'),
    (r'\bciencias\b', 'ciências'),
    (r'\bInvestigacion\b', 'Investigación'),
    (r'\binvestigacion\b', 'investigación'),
    (r'\bEdicion\b', 'Edición'),
    (r'\bedicion\b', 'edición'),
    (r'\bPublicacao\b', 'Publicação'),
    (r'\bpublicacao\b', 'publicação'),
    (r'\bComunicacao\b', 'Comunicação'),
    (r'\binformacao\b', 'informação'),
    (r'\bInformacao\b', 'Informação'),
    (r'\bAcao\b', 'Ação'),
    (r'\bacao\b', 'ação'),
    (r'\bPedagogica\b', 'Pedagógica'),
    (r'\bpedagogica\b', 'pedagógica'),
]

DIC_PONTE_TRILINGUE = {
    "educacao": "education educacion teaching pedagogy",
    "educacao musical": "music education educacion musical pedagogy",
    "musica": "music musica musical acoustics ethnomusicology",
    "saude": "health salud medicine medical clinical public health",
    "gestao": "management gestion administration business policy",
    "producao": "production produccion manufacturing industrial engineering",
    "engenharia": "engineering ingenieria technology technical",
    "computacao": "computing computer science informatica software artificial intelligence",
    "direito": "law derecho legal jurisprudence justice",
    "historia": "history historia historical heritage",
    "literatura": "literature literatura literary arts linguistics",
    "lingua": "language lengua linguistics philology",
    "biologia": "biology biologia biological genetics ecology",
    "fisica": "physics fisica physical optics quantum",
    "quimica": "chemistry quimica chemical materials",
    "matematica": "mathematics matematica mathematical algebra statistics",
    "economia": "economics economia economic finance market",
    "sociologia": "sociology sociologia social culture society",
    "psicologia": "psychology psicologia psychological mental behavioral",
    "filosofia": "philosophy filosofia philosophical ethics logic",
    "artes": "arts arte artistic visual music theater performance"
}

def expandir_texto_trilingue(txt):
    if not txt or not isinstance(txt, str):
        return ""
    norm = normalizar_texto(txt)
    palavras = norm.split()
    expansao = [txt]
    for p in palavras:
        if p in DIC_PONTE_TRILINGUE:
            expansao.append(DIC_PONTE_TRILINGUE[p])
    return " ".join(expansao)

def corrigir_ortografia_titulo(texto):
    if not texto or not isinstance(texto, str):
        return texto
    res = texto
    for pat, rep in REGRAS_ORTOGRAFIA:
        res = re.sub(pat, rep, res)
    return res

def normalizar_texto(txt):
    if not txt or not isinstance(txt, str):
        return ""
    nfkd = unicodedata.normalize('NFKD', txt)
    return "".join([c for c in nfkd if not unicodedata.combining(c)]).lower().strip()

def match_boolean_stem(texto_alvo, query):
    if not query or not query.strip():
        return True
        
    target_norm = normalizar_texto(texto_alvo)
    q_raw = query.strip()

    parts_not = re.split(r'\bNOT\b', q_raw, flags=re.IGNORECASE)
    pos_clause = parts_not[0]
    neg_clauses = parts_not[1:]

    for nc in neg_clauses:
        words_neg = [w for w in re.findall(r'\w+', normalizar_texto(nc)) if len(w) >= 3]
        for nw in words_neg:
            if nw in target_norm:
                return False

    or_clauses = re.split(r'\bOR\b', pos_clause, flags=re.IGNORECASE)
    for oc in or_clauses:
        and_clauses = re.split(r'\bAND\b', oc, flags=re.IGNORECASE)
        match_and = True
        for ac in and_clauses:
            phrases = re.findall(r'"([^"]+)"', ac)
            clean_ac = re.sub(r'"[^"]+"', '', ac)
            
            for ph in phrases:
                if normalizar_texto(ph) not in target_norm:
                    match_and = False
                    break
            if not match_and:
                continue

            words = [w for w in re.findall(r'\w+', normalizar_texto(clean_ac)) if w]
            for w in words:
                stem = w
                if len(w) > 4:
                    if w.endswith(('cao', 'tion', 'cion', 'ment', 'mento')):
                        stem = w[:-4]
                    elif w.endswith(('s', 'es', 'is', 'ia', 'ica', 'ico', 'ical', 'al')):
                        stem = w[:-2]
                
                if stem not in target_norm and w not in target_norm:
                    match_and = False
                    break

            if not match_and:
                break
        if match_and:
            return True
    return False

# ==========================================
# 🌐 DICIONÁRIO DE TRADUÇÃO TRILÍNGUE EXAUSTIVO (100%)
# ==========================================
DIC_TRANSLATE = {
    "English": {
        "titulo_pagina": "SciPubs - The Researcher's Portal",
        "titulo": "The Researcher's Portal",
        "subtitulo": "Open science matters. No questions. No fees. No ads. Just use.",
        "nav_tit": "Navigation Panel",
        "indexadores_tit": "DATABASES",
        "repositorios_tit": "REPOSITORIES",
        "ia_tit": "ACADEMIC AI",
        "gov_tit": "GOVERNMENT SITES",
        "inst_tit": "INSTITUTIONAL INFO",
        "pessoal_lbl": "Personal website",
        "cat_capes_lbl": "CAPES Catalog",
        "lattes_lbl": "Lattes Curriculum",
        "periodicos_capes_lbl": "CAPES Journal Portal",
        "musica_ufop_lbl": "Music-UFOP",
        "copyright_tit": "Copyright & Ownership:",
        "copyright_desc": "© 2026 João F. Soares-Quadros Jr.\nFederal University of Ouro Preto\nMinas Gerais, Brazil.\nAll rights reserved.",
        "busca_cat": "🔎 Journal Finder",
        "busca_ia": "Smart Recommender (AI)",
        "fale_conosco": "Contact Us",
        "doacoes": "☕ Donate",
        "inscrever": "✉️ Subscribe",
        "baixar_win": "💻 Download Windows Version",
        "sobre_tit": "💡 About SciPubs & How to Use",
        "sobre_head": "Welcome to SciPubs: The Researcher's Portal!",
        "sobre_sub": "This tool was developed to optimize the search for high-impact scientific journals.",
        "sobre_what": "What can you do here?",
        "item1_title": "1. Advanced & Boolean Search: ",
        "item1_desc1": "Search for exact phrases using quotation marks (e.g., ",
        "item1_desc2": " ) or combine multiple criteria using the logical operators ",
        "item1_desc3": " (e.g., ",
        "item1_desc4": " ).",
        "item2_title": "2. Filter by Subarea (CNPq): ",
        "item2_desc": "Find journals perfectly aligned with your specific subarea of expertise.",
        "item3_title": "3. Impact Metrics: ",
        "item3_desc": "Analyze international prestige through consolidated quartiles and indicators from JCR (Clarivate), SJR (Scopus), H-Index, and direct links to the h5-Index (Google Scholar).",
        "item4_title": "4. Smart Recommender (AI): ",
        "item4_desc": "Paste your title and abstract, and let the AI recommend the best matching journals with specific thematic rationale and direct links.",
        "item5_title": "5. Data Export: ",
        "item5_desc": "Filter or check journals of interest and download your customized table immediately.",
        "cat_tit": "Journal Catalog",
        "placeholder_busca": "Type journal title, ISSN, or keyword (Supports AND, OR, NOT, and \"exact phrases\")...",
        "grande_area_lbl": "Broad Area",
        "area_lbl": "Knowledge Area",
        "cat_lbl": "Category / Knowledge Subarea",
        "bases_lbl": "Databases",
        "quartil_jcr_lbl": "JCR Quartile",
        "quartil_sjr_lbl": "SJR Quartile",
        "ordenar_lbl": "Sort results by",
        "itens_pag_lbl": "Display per page",
        "h_lbl": "H-Index",
        "pesquisar": "Search",
        "todas": "All",
        "todos": "All",
        "nao_informado": "Not provided",
        "geral": "General",
        "multidisciplinar": "Multidisciplinary",
        "ia_titulo": "Hybrid Recommendation Engine (AI + TF-IDF)",
        "ia_subtitulo": "Paste your article title and abstract. Our Hybrid Transformer + TF-IDF engine suggests top matching journals.",
        "ia_campo_titulo": "Article Title / Manuscript",
        "ia_campo_resumo": "Abstract (Supports Portuguese, English, or Spanish)",
        "ia_gemini_key": "Gemini Key (optional)",
        "ia_gemini_hint": "Leave blank to use local Ollama or local algorithm",
        "ia_gemini_status": "🔑 Gemini API key configured",
        "ia_btn_gerar": "Analyze and Recommend",
        "ai_engine_tit": "AI Engine",
        "ai_engine_sub": "Hybrid Recommendations (SentenceTransformer + TF-IDF + Indexers).",
        "about_modes_tit": "About AI modes",
        "how_gemini_tit": "How to get a free Gemini key?",
        "refine_targets": "Refine Search by Database",
        "database_ia_lbl": "Database (IA)",
        "num_recs_lbl": "Number of desired recommendations (max. 20)",
        "acesse_site": "Visit Website",
        "ver_h5": "View h5-Index",
        "fechar": "Close",
        "sub_modal_tit": "Join our VIP Community! 🚀",
        "sub_modal_desc": "Leave your email to receive publication tips and platform updates. No spam, we promise.",
        "nome": "Full Name:",
        "email": "Email:",
        "doacao_modal_tit": "Support SciPubs!",
        "doacao_modal_desc": (
            "Your voluntary donation is essential for us to keep our servers active and continue developing "
            "new technological tools for the global scientific community.\n\n"
            "We use Buy Me a Coffee, a secure international platform ($5 per coffee)."
        ),
        "link_doacao": "Click here to donate via Buy Me a Coffee",
        "lang_lbl": "Language / Idioma:",
        "sem_resultados": "No journals found matching the specified search criteria.",
        "alerta_ia": "Please enter the manuscript title and/or abstract to generate recommendations.",
        "baixar_csv": "Download (.csv)",
        "baixar_excel": "Download (.xlsx)",
        "selecionados": "selected",
        "pag_anterior": "Previous",
        "pag_proxima": "Next",
        "pagina_fmt": "Page {atual} of {total} ({total_itens} records found)",
        "snack_msg": "✅ File {fname} successfully generated! If download does not start, check browser pop-up permissions.",
        "prob_aceitacao": "Acceptance Prob.",
        "exp1_items": [
            "AI semantically analyzes your title and abstract",
            "Cross-references with local catalog and academic databases (OpenAlex)",
            "Returns recommendations with enriched metrics",
            "For faster results, you can insert a Gemini AI API key; the step-by-step guide to obtain it for free is explained below.",
            "If you don't have or don't want to use this option, you can run the search leaving this field blank and using Ollama (Llama 3) as the AI."
        ],
        "exp2_items": [
            "Access aistudio.google.com",
            "Log in with your Google account",
            "Click on \"Get API Key\" → \"Create API Key\"",
            "Copy the key and paste it above"
        ],
        "areas": ["All", "Exact and Earth Sciences", "Biological Sciences", "Engineering", "Health Sciences", "Agricultural Sciences", "Applied Social Sciences", "Human Sciences", "Linguistics, Letters and Arts"],
        "ordem_opts": [
            "% Match (highest to lowest)",
            "% Acceptance Probability (highest to lowest)",
            "Title (A-Z)",
            "Title (Z-A)"
        ]
    },
    "Português": {
        "titulo_pagina": "SciPubs - O Portal do Pesquisador",
        "titulo": "O Portal do Pesquisador",
        "subtitulo": "A ciência aberta importa. Sem perguntas. Sem taxas. Sem anúncios. Apenas use.",
        "nav_tit": "Painel de Navegação",
        "indexadores_tit": "BASES DE DADOS",
        "repositorios_tit": "REPOSITÓRIOS",
        "ia_tit": "IA ACADÊMICA",
        "gov_tit": "SITES GOVERNAMENTAIS",
        "inst_tit": "INFORMAÇÕES INSTITUCIONAIS",
        "pessoal_lbl": "Site pessoal",
        "cat_capes_lbl": "Catálogo da CAPES",
        "lattes_lbl": "Currículo Lattes",
        "periodicos_capes_lbl": "Portal de Periódicos CAPES",
        "musica_ufop_lbl": "Música-UFOP",
        "copyright_tit": "Direitos Autorais:",
        "copyright_desc": "© 2026 João F. Soares-Quadros Jr.\nUniversidade Federal de Ouro Preto\nMinas Gerais, Brasil.\nTodos os direitos reservados.",
        "busca_cat": "🔎 Buscador de Periódicos",
        "busca_ia": "Recomendador Inteligente Híbrido (IA + TF-IDF)",
        "fale_conosco": "Fale conosco",
        "doacoes": "☕ Doações",
        "inscrever": "✉️ Inscrever-se",
        "baixar_win": "💻 Baixar Versão para Windows",
        "sobre_tit": "💡 Sobre o SciPubs & Como Usar",
        "sobre_head": "Bem-vindo ao SciPubs: O Portal do Pesquisador!",
        "sobre_sub": "Ferramenta desenvolvida para otimizar a busca por periódicos científicos de alto impacto.",
        "sobre_what": "O que você pode fazer aqui?",
        "item1_title": "1. Busca Avançada & Booleana: ",
        "item1_desc1": "Pesquise por expressões exatas usando aspas (ex: ",
        "item1_desc2": " ) ou combine múltiplos critérios usando os operadores lógicos ",
        "item1_desc3": " (ex: ",
        "item1_desc4": " ).",
        "item2_title": "2. Filtro por Subárea (CNPq): ",
        "item2_desc": "Encontre periódicos perfeitamente alinhados com a sua subárea específica de conhecimento.",
        "item3_title": "3. Métricas de Impacto: ",
        "item3_desc": "Analise o prestígio internacional através de quartis e indicadores consolidados do JCR (Clarivate), SJR (Scopus), Índice-H e acesse o link para o Índice-h5 (Google Acadêmico).",
        "item4_title": "4. Recomendador Inteligente (IA): ",
        "item4_desc": "Cole o título e resumo do seu artigo e deixe a IA recomendar as melhores opções com justificativa temática e links para os sites.",
        "item5_title": "5. Exportação de Dados: ",
        "item5_desc": "Filtre ou selecione as revistas de seu interesse e faça o download da tabela personalizada imediatamente.",
        "cat_tit": "Catálogo de Periódicos",
        "placeholder_busca": "Digite o título da revista, ISSN ou palavra-chave (Suporta AND, OR, NOT e \"frases exatas\")...",
        "grande_area_lbl": "Grande Área",
        "area_lbl": "Área do Conhecimento",
        "cat_lbl": "Categoria / Subárea do Conhecimento",
        "bases_lbl": "Bases de dados",
        "quartil_jcr_lbl": "Quartil JCR",
        "quartil_sjr_lbl": "Quartil SJR",
        "ordenar_lbl": "Ordenar resultados por",
        "itens_pag_lbl": "Exibir por página",
        "h_lbl": "Índice H",
        "pesquisar": "Pesquisar",
        "todas": "Todas",
        "todos": "Todos",
        "nao_informado": "Não informado",
        "geral": "Geral",
        "multidisciplinar": "Multidisciplinar",
        "ia_titulo": "Recomendação Temática Híbrida (IA Transformer + TF-IDF)",
        "ia_subtitulo": "Cole o título e o resumo do seu artigo. Nosso motor híbrido de IA (SentenceTransformer + TF-IDF) analisa seu conteúdo e sugere as melhores revistas com métricas enriquecidas.",
        "ia_campo_titulo": "Título do Artigo / Manuscrito",
        "ia_campo_resumo": "Resumo / Abstract (Suporta Português, Inglês ou Espanhol)",
        "ia_gemini_key": "Chave Gemini (opcional)",
        "ia_gemini_hint": "Deixe em branco para usar Ollama local ou algoritmo local",
        "ia_gemini_status": "🔑 Chave API do Gemini configurada",
        "ia_btn_gerar": "Analisar e Recomendar",
        "ai_engine_tit": "Motor Híbrido de IA",
        "ai_engine_sub": "Recomendações de Alta Precisão (SentenceTransformer + TF-IDF + Indexadores).",
        "about_modes_tit": "Sobre os modos de IA",
        "how_gemini_tit": "Como obter chave Gemini gratuita?",
        "refine_targets": "Refinar Pesquisa por Base de Dados",
        "database_ia_lbl": "Base de dados (IA)",
        "num_recs_lbl": "Quantidade de recomendações desejadas (máx. 20)",
        "acesse_site": "Acesse o site",
        "ver_h5": "Ver Índice-H5",
        "fechar": "Fechar",
        "sub_modal_tit": "Join our VIP Community! 🚀",
        "sub_modal_desc": "Leave your email to receive publication tips and platform updates. No spam, we promise.",
        "nome": "Full Name:",
        "email": "Email:",
        "doacao_modal_tit": "Apoie o SciPubs!",
        "doacao_modal_desc": (
            "A sua doação voluntária é fundamental para mantermos os nossos servidores ativos e continuarmos "
            "desenvolvendo novas ferramentas tecnológicas para a comunidade acadêmica e científica.\n\n"
            "Nós utilizamos o Buy Me a Coffee, uma plataforma internacional segura ($5 por café)."
        ),
        "link_doacao": "Clique aqui para doar pelo Buy Me a Coffee",
        "lang_lbl": "Language / Idioma:",
        "sem_resultados": "Nenhum periódico encontrado com os critérios fornecidos.",
        "alerta_ia": "Digite o título e/ou resumo do manuscrito para gerar a recomendação.",
        "baixar_csv": "Download (.csv)",
        "baixar_excel": "Download (.xlsx)",
        "selecionados": "selecionados",
        "pag_anterior": "Anterior",
        "pag_proxima": "Próxima",
        "pagina_fmt": "Página {atual} de {total} ({total_itens} registros encontrados)",
        "snack_msg": "✅ Arquivo {fname} gerado com sucesso! Se o download não iniciar, verifique a permissão de pop-up do navegador.",
        "prob_aceitacao": "Prob. Aceitação",
        "exp1_items": [
            "A IA analisa semanticamente seu título e resumo usando SentenceTransformers e TF-IDF",
            "Cruza com o catálogo local e bases acadêmicas (OpenAlex)",
            "Retorna recomendações de máxima precisão temáticas e indexadores",
            "Para obter resultados mais ágeis, você pode inserir uma chave API do Gemini AI; o passo a passo para a obtenção gratuita é explicado abaixo.",
            "Caso não tenha ou não queira usar essa opção, você poderá realizar a busca deixando em branco essa janela e usando o Ollama (Llama 3) como IA."
        ],
        "exp2_items": [
            "Acesse aistudio.google.com",
            "Faça login com sua conta Google",
            "Clique em \"Get API Key\" → \"Create API Key\"",
            "Copie a chave e cole acima"
        ],
        "areas": ["Todas", "Ciências Exatas e da Terra", "Ciências Biológicas", "Engenharias", "Ciências da Saúde", "Ciências Agrárias", "Ciências Sociais Aplicadas", "Ciências Humanas", "Linguística, Letras e Artes"],
        "ordem_opts": [
            "% de Match (maior para o menor)",
            "% Probabilidade de aceitação (maior para a menor)",
            "Título (A-Z)",
            "Título (Z-A)"
        ]
    },
    "Español": {
        "titulo_pagina": "SciPubs - El Portal del Investigador",
        "titulo": "El Portal del Investigador",
        "subtitulo": "La ciencia abierta importa. Sin preguntas. Sin tasas. Sin anuncios. Sólo úsela.",
        "nav_tit": "Panel de Navegación",
        "indexadores_tit": "BASES DE DATOS",
        "repositorios_tit": "REPOSITORIOS",
        "ia_tit": "IA ACADÉMICA",
        "gov_tit": "SITIOS GUBERNAMENTALES",
        "inst_tit": "INFORMACIÓN INSTITUCIONAL",
        "pessoal_lbl": "Sitio personal",
        "cat_capes_lbl": "Catálogo de CAPES",
        "lattes_lbl": "Currículo Lattes",
        "periodicos_capes_lbl": "Portal de Revistas CAPES",
        "musica_ufop_lbl": "Música-UFOP",
        "copyright_tit": "Derechos de Autor:",
        "copyright_desc": "© 2026 João F. Soares-Quadros Jr.\nUniversidad Federal de Ouro Preto\nMinas Gerais, Brasil.\nTodos los derechos reservados.",
        "busca_cat": "🔎 Buscador de Revistas",
        "busca_ia": "Recomendador Inteligente Híbrido (IA + TF-IDF)",
        "fale_conosco": "Contáctenos",
        "doacoes": "☕ Donaciones",
        "inscrever": "✉️ Suscribirse",
        "baixar_win": "💻 Descargar Versión para Windows",
        "sobre_tit": "💡 Sobre SciPubs y Cómo Usar",
        "sobre_head": "¡Bienvenido a SciPubs: El Portal del Investigador!",
        "sobre_sub": "Esta herramienta fue desarrollada para optimizar la búsqueda de revistas científicas de alto impacto.",
        "sobre_what": "¿Qué puedes hacer aquí?",
        "item1_title": "1. Búsqueda Avanzada y Buleana: ",
        "item1_desc1": "Busque frases exactas usando comillas (ej.: ",
        "item1_desc2": " ) o combine múltiples criterios usando los operadores lógicos ",
        "item1_desc3": " (ej.: ",
        "item1_desc4": " ).",
        "item2_title": "2. Filtro por Subárea (CNPq): ",
        "item2_desc": "Encuentre revistas perfectamente alineadas con su subárea específica de conocimiento.",
        "item3_title": "3. Métricas de Impacto: ",
        "item3_desc": "Analice el prestigio internacional a través de cuartiles e indicadores consolidados de JCR (Clarivate), SJR (Scopus), Índice-H y enlace al Índice-h5 (Google Académico).",
        "item4_title": "4. Recomendador Inteligente (IA): ",
        "item4_desc": "Pegue el título y resumen de su artículo y deje que la IA le recomiende las mejores opciones con justificación temática y enlaces.",
        "item5_title": "5. Exportación de Datos: ",
        "item5_desc": "Filtre o seleccione las revistas de su interés y descargue la tabla personalizada inmediatamente.",
        "cat_tit": "Catálogo de Revistas",
        "placeholder_busca": "Ingrese el título de la revista, ISSN o palabra clave (Soporta AND, OR, NOT e \"frases exactas\")...",
        "grande_area_lbl": "Gran Área",
        "area_lbl": "Área del Conocimiento",
        "cat_lbl": "Categoría / Subárea del Conocimiento",
        "bases_lbl": "Bases de datos",
        "quartil_jcr_lbl": "Cuartil JCR",
        "quartil_sjr_lbl": "Quartil SJR",
        "ordenar_lbl": "Ordenar resultados por",
        "itens_pag_lbl": "Mostrar por página",
        "h_lbl": "Índice H",
        "pesquisar": "Buscar",
        "todas": "Todas",
        "todos": "Todos",
        "nao_informado": "No informado",
        "geral": "General",
        "multidisciplinar": "Multidisciplinar",
        "ia_titulo": "Recomendación Temática Híbrida (IA Transformer + TF-IDF)",
        "ia_subtitulo": "Pegue el título y el resumen de su artículo. Nuestro motor híbrido de IA (SentenceTransformer + TF-IDF) sugiere las mejores revistas.",
        "ia_campo_titulo": "Título del Artículo / Manuscrito",
        "ia_campo_resumo": "Resumen / Abstract (Soporta Portugués, Inglés o Español)",
        "ia_gemini_key": "Clave Gemini (opcional)",
        "ia_gemini_hint": "Deje en blanco para usar Ollama local o algoritmo local",
        "ia_gemini_status": "🔑 Clave API de Gemini configurada",
        "ia_btn_gerar": "Analizar y Recomendar",
        "ai_engine_tit": "Motor Híbrido de IA",
        "ai_engine_sub": "Recomendaciones de Alta Precisión (SentenceTransformer + TF-IDF + Indexadores).",
        "about_modes_tit": "Sobre los modos de IA",
        "how_gemini_tit": "¿Cómo obtener clave Gemini gratuita?",
        "refine_targets": "Refinar Búsqueda por Base de Datos",
        "database_ia_lbl": "Bases de datos (IA)",
        "num_recs_lbl": "Cantidad de recomendaciones deseadas (máx. 20)",
        "acesse_site": "Visitar sitio",
        "ver_h5": "Ver Índice-H5",
        "fechar": "Cerrar",
        "sub_modal_tit": "¡Únete a nuestra Comunidad VIP! 🚀",
        "sub_modal_desc": "Deje su correo electrónico para recibir consejos de publicación y actualizaciones. Prometemos: cero spam.",
        "nome": "Nombre Completo:",
        "email": "Correo Electrónico:",
        "doacao_modal_tit": "¡Apoye a SciPubs!",
        "doacao_modal_desc": (
            "Su donación voluntaria es fundamental para mantener nuestros servidores activos y continuar "
            "desarrollando nuevas herramientas tecnológicas para la comunidad científica.\n\n"
            "Utilizamos Buy Me a Coffee, una plataforma internacional segura ($5 por café)."
        ),
        "link_doacao": "Haga clic aquí para donar a través de Buy Me a Coffee",
        "lang_lbl": "Language / Idioma:",
        "sem_resultados": "No se encontraron revistas con los criterios especificados.",
        "alerta_ia": "Por favor, ingrese el título y/o resumen del manuscrito para generar las recomendaciones.",
        "baixar_csv": "Download (.csv)",
        "baixar_excel": "Download (.xlsx)",
        "selecionados": "seleccionados",
        "pag_anterior": "Anterior",
        "pag_proxima": "Siguiente",
        "pagina_fmt": "Página {atual} de {total} ({total_itens} registros encontrados)",
        "snack_msg": "✅ ¡Archivo {fname} generado con éxito! Si la descarga no inicia, verifique los permisos de ventanas emergentes.",
        "prob_aceitacao": "Prob. Aceptación",
        "exp1_items": [
            "La IA analiza semánticamente su título y resumen usando SentenceTransformers y TF-IDF",
            "Cruza con el catálogo local y bases académicas (OpenAlex)",
            "Devuelve recomendaciones de máxima precisión temáticas y indexadores",
            "Para obtener resultados más ágiles, puede insertar una clave API de Gemini AI; el paso a paso para obtenerla gratis se explica a continuación.",
            "Si no tiene o no desea usar esta opción, puede realizar la búsqueda dejando este campo en blanco y usando Ollama (Llama 3) como IA."
        ],
        "exp2_items": [
            "Ingrese a aistudio.google.com",
            "Inicie sesión con su cuenta de Google",
            "Haga clic en \"Get API Key\" → \"Create API Key\"",
            "Copie la clave y péguela arriba"
        ],
        "areas": ["Todas", "Ciencias Exactas y de la Tierra", "Ciencias Biológicas", "Ingenierías", "Ciencias de la Salud", "Ciencias Agrarias", "Ciencias Sociales Aplicadas", "Ciencias Humanas", "Lingüística, Letras y Artes"],
        "ordem_opts": [
            "% de Match (mayor a menor)",
            "% Probabilidad de aceptación (mayor a menor)",
            "Título (A-Z)",
            "Título (Z-A)"
        ]
    }
}

BASES_DADOS_OPCOES = [
    "Todas",
    "Web of Science",
    "Scopus",
    "Scielo",
    "Educ@"
]

def safe_float(val):
    if pd.isna(val) or val is None:
        return 0.0
    val_str = str(val).strip().replace(",", ".")
    if val_str in ["", "-", "nan", "none", "None"]:
        return 0.0
    try:
        return float(val_str)
    except ValueError:
        return 0.0

def get_s_index(indexer_str):
    if pd.isna(indexer_str) or not isinstance(indexer_str, str) or not indexer_str.strip():
        return 0.0
    tokens = [t.strip() for t in re.split(r'[,;\-\s]+', indexer_str.lower()) if t.strip()]
    scores = [0.0]
    if "scie" in tokens or "ssci" in tokens: scores.append(1.0)
    if "scopus" in tokens: scores.append(0.8)
    if "ahci" in tokens or "achi" in tokens: scores.append(0.7)
    if "scielo" in tokens: scores.append(0.6)
    if "esci" in tokens: scores.append(0.5)
    if "educ@" in tokens or "educa" in tokens: scores.append(0.4)
    return max(scores)

@functools.lru_cache(maxsize=1)
def carregar_modelo_transformer():
    if not HAS_SENTENCE_TRANSFORMERS or SentenceTransformer is None:
        return None
    try:
        return SentenceTransformer("all-MiniLM-L6-v2")
    except Exception as e:
        print(f"[AVISO] Não foi possível carregar SentenceTransformer: {e}")
        return None

@functools.lru_cache(maxsize=1)
def carregar_dense_embeddings_cache():
    if os.path.exists(CACHE_PATH):
        try:
            with open(CACHE_PATH, "rb") as f:
                return pickle.load(f)
        except Exception as e:
            print(f"[AVISO] Falha ao carregar cache de embeddings: {e}")
    return None

class SciPubsDataEngine:
    """Motor de Dados Híbrido (SentenceTransformer + TF-IDF + Indexadores) do SciPubs"""
    def __init__(self):
        self.df = None
        self.df_original = None
        self.total_revistas = 33921
        self.vectorizer = None
        self.tfidf_matrix = None
        self.transformer_model = None
        self.dense_embeddings = None
        self.load_data()

    def load_data(self):
        caminhos = [
            DADOS_CSV_PATH,
            DATA_PATH if 'DATA_PATH' in globals() else "",
            os.path.join(STREAMLIT_DIR, "dados.csv"),
            os.path.join(BASE_DIR, "dados.csv"),
            "dados.csv"
        ]
        
        caminho_final = None
        for p in caminhos:
            if p and os.path.exists(p):
                caminho_final = p
                break
                
        if caminho_final:
            try:
                df_raw = pd.read_csv(caminho_final, dtype=str, encoding="utf-8-sig", low_memory=False, on_bad_lines="skip").fillna("")
                df_raw = df_raw.loc[:, ~df_raw.columns.duplicated()]
                self.df_original = df_raw.copy()

                rename_map = {}
                for col in df_raw.columns:
                    c = str(col).lower().strip()
                    if ("t" in c and "tulo" in c) or "title" in c or "revista" in c or "periodico" in c:
                        rename_map[col] = "titulo"
                    elif "issn" in c:
                        rename_map[col] = "issn"
                    elif "aims" in c or "escopo" in c or "scope" in c:
                        rename_map[col] = "escopo"
                    elif "grande" in c:
                        rename_map[col] = "grande_area"
                    elif "categoria" in c or "subarea" in c or "subárea" in c:
                        rename_map[col] = "categoria"
                    elif "conhecimento" in c or "area" in c or "área" in c:
                        rename_map[col] = "area"
                    elif "quartil jcr" in c or "jcr quartil" in c or "jcr quartile" in c:
                        rename_map[col] = "quartil_jcr"
                    elif "sjr best" in c or "sjr quartile" in c or "quartil sjr" in c:
                        rename_map[col] = "quartil_sjr"
                    elif "index-h5" in c or "h5" in c:
                        rename_map[col] = "h5_link"
                    elif "index-h" in c or "h-index" in c:
                        rename_map[col] = "h_index"
                    elif "jif" in c or "fator" in c or "impact" in c:
                        rename_map[col] = "jif"
                    elif "sjr" in c:
                        rename_map[col] = "sjr"
                    elif "indexador" in c:
                        rename_map[col] = "indexador"
                    elif "home" in c or "url" in c or "site" in c:
                        rename_map[col] = "homepage"

                df_raw.rename(columns=rename_map, inplace=True)
                df_raw = df_raw.loc[:, ~df_raw.columns.duplicated()]

                for c_name in ["titulo", "issn", "escopo", "grande_area", "area", "categoria", "h5_link", "h_index", "jif", "sjr", "quartil_jcr", "quartil_sjr", "indexador", "homepage"]:
                    if c_name not in df_raw.columns:
                        df_raw[c_name] = "-"

                df_raw["titulo"] = df_raw["titulo"].apply(corrigir_ortografia_titulo)
                
                df_raw["search_text"] = (
                    df_raw["titulo"].astype(str) + " " +
                    df_raw["issn"].astype(str) + " " +
                    df_raw["grande_area"].astype(str) + " " +
                    df_raw["area"].astype(str) + " " +
                    df_raw["categoria"].astype(str) + " " +
                    df_raw["indexador"].astype(str) + " " +
                    df_raw["escopo"].astype(str)
                )
                        
                self.df = df_raw
                self.total_revistas = len(self.df)
                print(f"[OK] Base dados.csv carregada e normalizada! Total de periodicos: {self.total_revistas:,}")
                
                # 📌 MOTOR SPARSE TF-IDF
                textos_completos = (
                    self.df["escopo"].astype(str) + " " +
                    self.df["escopo"].astype(str) + " " +
                    self.df["escopo"].astype(str) + " " +
                    self.df["titulo"].astype(str) + " " +
                    self.df["area"].astype(str)
                ).fillna("")
                
                self.vectorizer = TfidfVectorizer(max_features=16000, stop_words='english')
                self.tfidf_matrix = self.vectorizer.fit_transform(textos_completos)
                print("[OK] Vetorizador TF-IDF inicializado.")

                # 📌 MOTOR DENSE SENTENCETRANSFORMER
                self.transformer_model = carregar_modelo_transformer()
                self.dense_embeddings = carregar_dense_embeddings_cache()
                if self.dense_embeddings is not None:
                    print(f"[OK] Cache de embeddings densos carregado: {len(self.dense_embeddings):,} vetores.")
            except Exception as e:
                print(f"[ERRO] Falha ao carregar dados.csv: {e}")
                self.df = pd.DataFrame()
                self.df_original = pd.DataFrame()
        else:
            print("[AVISO] dados.csv nao encontrado.")
            self.df = pd.DataFrame()
            self.df_original = pd.DataFrame()

    def recomendar_manuscrito(self, titulo, resumo, area_filtro="Todas", ordenacao_idx=0, limite=20):
        if self.df is None or self.df.empty:
            return []

        # 📌 PREPARAÇÃO DO MANUSCRITO (TRÊS VEZES O TÍTULO)
        texto_trilingue = expandir_texto_trilingue(f"{titulo} {resumo}")
        texto_artigo = f"{titulo} {titulo} {titulo} {resumo} {texto_trilingue}"

        df_calc = self.df.copy()

        # 1. CÁLCULO DE SIMILARIDADE DENSA (SENTENCETRANSFORMER)
        if self.transformer_model is not None and self.dense_embeddings is not None:
            vec_dense = self.transformer_model.encode([texto_artigo], convert_to_numpy=True)
            n_rows = len(df_calc)
            emb_subset = self.dense_embeddings[:n_rows]
            sim_dense = cosine_similarity(vec_dense, emb_subset).flatten()
            sim_dense = np.nan_to_num(sim_dense, nan=0.0)
        else:
            sim_dense = np.zeros(len(df_calc))

        # 2. CÁLCULO DE SIMILARIDADE ESPARSA (TF-IDF)
        if self.vectorizer is not None:
            vec_sparse = self.vectorizer.transform([texto_artigo])
            sim_sparse = cosine_similarity(vec_sparse, self.tfidf_matrix).flatten()
            sim_sparse = np.nan_to_num(sim_sparse, nan=0.0)
        else:
            sim_sparse = np.zeros(len(df_calc))

        # 3. CÁLCULO DO SCORE DO INDEXADOR (SCIE/SSCI=1.0, SCOPUS=0.8, AHCI=0.7, SCIELO=0.6, ESCI=0.5, EDUC@=0.4)
        s_index = np.array([get_s_index(x) for x in df_calc["indexador"]])

        # 4. REFINAMENTO DE BUSCA POR BASE DE DADOS
        if area_filtro and area_filtro not in ["Todas", "All"]:
            db_k = area_filtro.lower()
            if "web of science" in db_k or "wos" in db_k:
                mask_db = df_calc["indexador"].astype(str).str.lower().str.contains("web of science|wos", regex=True, na=False)
            elif "scopus" in db_k:
                mask_db = df_calc["indexador"].astype(str).str.lower().str.contains("scopus", na=False)
            elif "scielo" in db_k:
                mask_db = df_calc["indexador"].astype(str).str.lower().str.contains("scielo", na=False)
            elif "educ" in db_k:
                mask_db = df_calc["indexador"].astype(str).str.lower().str.contains("educa|educ@", regex=True, na=False)
            else:
                mask_db = df_calc["indexador"].astype(str).str.contains(area_filtro, case=False, na=False)
            
            df_calc = df_calc[mask_db].copy()
            idx_validos = df_calc.index
            sim_dense = sim_dense[idx_validos]
            sim_sparse = sim_sparse[idx_validos]
            s_index = s_index[idx_validos]

        # 📌 SCORE FUSÃO HÍBRIDA FINAL: 65% Dense (Transformer) + 15% Sparse (TF-IDF) + 20% Indexador
        if self.transformer_model is not None and self.dense_embeddings is not None:
            score_final = (0.65 * sim_dense + 0.15 * sim_sparse + 0.20 * s_index) * 100.0
        else:
            score_final = (0.80 * sim_sparse + 0.20 * s_index) * 100.0

        df_calc["S_text"] = sim_dense if (self.transformer_model is not None and self.dense_embeddings is not None) else sim_sparse
        df_calc["S_sparse"] = sim_sparse
        df_calc["S_index"] = s_index
        df_calc["Score_final"] = score_final

        # 📌 FATOR DE IMPACTO PARA DESEMPATE MULTINÍVEL (MAX JIF / SJR)
        df_calc["jif_num"] = df_calc["jif"].apply(safe_float)
        df_calc["sjr_num"] = df_calc["sjr"].apply(safe_float)
        df_calc["fator_impacto"] = np.maximum(df_calc["jif_num"], df_calc["sjr_num"])

        # 📌 PROBABILIDADE PROXY DE ACEITAÇÃO (%)
        def calcular_prob_aceitacao(row):
            s_text = row["S_text"]
            jif_val = row["fator_impacto"]
            
            q_jcr = str(row["quartil_jcr"]).upper()
            dificuldade_q = 0.85 if "Q1" in q_jcr else (0.65 if "Q2" in q_jcr else (0.45 if "Q3" in q_jcr else 0.25))
            dificuldade_jif = min(1.0, jif_val / 10.0)
            
            dificuldade = 0.40 * dificuldade_jif + 0.35 * dificuldade_q + 0.25 * (1.0 - s_text)
            prob = (s_text * 0.65 + (1.0 - dificuldade) * 0.35) * 100.0
            return int(min(82, max(12, round(prob))))

        df_calc["Prob_aceitacao"] = df_calc.apply(calcular_prob_aceitacao, axis=1)

        # 📌 ORDENAÇÃO MULTINÍVEL
        if ordenacao_idx == 0:
            df_sorted = df_calc.sort_values(by=["Score_final", "fator_impacto", "S_text"], ascending=[False, False, False])
        elif ordenacao_idx == 1:
            df_sorted = df_calc.sort_values(by=["Prob_aceitacao", "Score_final", "fator_impacto"], ascending=[False, False, False])
        elif ordenacao_idx == 2:
            df_sorted = df_calc.sort_values(by="titulo", ascending=True)
        elif ordenacao_idx == 3:
            df_sorted = df_calc.sort_values(by="titulo", ascending=False)

        res_final = df_sorted.head(limite)
        return res_final.to_dict(orient="records")

    def buscar_geral(self, termo="", grande_area="Todas", base_dados="Todas", quartil_jcr="Todos", quartil_sjr="Todos", ordenacao="titulo_asc", limite=1000):
        if self.df is None or self.df.empty:
            return []

        df_filtered = self.df.copy()

        if termo and termo.strip():
            df_filtered = df_filtered[df_filtered["search_text"].apply(lambda text: match_boolean_stem(text, termo))]

        if grande_area and grande_area not in ["Todas", "All"]:
            df_filtered = df_filtered[df_filtered["grande_area"].astype(str).str.contains(grande_area, case=False, na=False) | df_filtered["area"].astype(str).str.contains(grande_area, case=False, na=False)]

        if base_dados and base_dados not in ["Todas", "All"]:
            db_k = base_dados.lower()
            if "web of science" in db_k or "wos" in db_k:
                df_filtered = df_filtered[df_filtered["indexador"].astype(str).str.lower().str.contains("web of science|wos", regex=True, na=False)]
            elif "scopus" in db_k:
                df_filtered = df_filtered[df_filtered["indexador"].astype(str).str.lower().str.contains("scopus", na=False)]
            elif "scielo" in db_k:
                df_filtered = df_filtered[df_filtered["indexador"].astype(str).str.lower().str.contains("scielo", na=False)]
            elif "educ" in db_k:
                df_filtered = df_filtered[df_filtered["indexador"].astype(str).str.lower().str.contains("educa|educ@", regex=True, na=False)]
            else:
                df_filtered = df_filtered[df_filtered["indexador"].astype(str).str.contains(base_dados, case=False, na=False)]

        if quartil_jcr and quartil_jcr not in ["Todos", "All"]:
            df_filtered = df_filtered[df_filtered["quartil_jcr"].astype(str).str.upper().str.contains(quartil_jcr.upper(), na=False)]

        if quartil_sjr and quartil_sjr not in ["Todos", "All"]:
            df_filtered = df_filtered[df_filtered["quartil_sjr"].astype(str).str.upper().str.contains(quartil_sjr.upper(), na=False)]

        if ordenacao in ["titulo_asc", 0]:
            df_filtered = df_filtered.sort_values(by="titulo", ascending=True)
        elif ordenacao in ["titulo_desc", 1]:
            df_filtered = df_filtered.sort_values(by="titulo", ascending=False)
        elif ordenacao in ["database", 2]:
            df_filtered = df_filtered.sort_values(by="indexador", ascending=True)
        elif ordenacao in ["jif_desc", 3]:
            df_filtered["jif_num"] = pd.to_numeric(df_filtered["jif"].str.replace(",", "."), errors="coerce").fillna(0)
            df_filtered = df_filtered.sort_values(by="jif_num", ascending=False)
        elif ordenacao in ["sjr_desc", 4]:
            df_filtered["sjr_num"] = pd.to_numeric(df_filtered["sjr"].str.replace(",", "."), errors="coerce").fillna(0)
            df_filtered = df_filtered.sort_values(by="sjr_num", ascending=False)
        elif ordenacao in ["h_index_desc", 5]:
            df_filtered["h_num"] = pd.to_numeric(df_filtered["h_index"], errors="coerce").fillna(0)
            df_filtered = df_filtered.sort_values(by="h_num", ascending=False)

        return df_filtered.head(limite).to_dict(orient="records")


def abrir_link(page: ft.Page, url: str, termo_fallback: str = ""):
    u_final = None
    if url and isinstance(url, str):
        u = url.strip()
        if u and u not in ["-", "None", "nan", ""]:
            if not u.startswith("http://") and not u.startswith("https://") and not u.startswith("mailto:"):
                u = "https://" + u
            u_final = u

    if not u_final and termo_fallback:
        q = urllib.parse.quote(termo_fallback)
        u_final = f"https://www.google.com/search?q={q}"

    if u_final:
        try:
            webbrowser.open(u_final, new=2)
        except Exception:
            pass
        try:
            page.launch_url(u_final, web_window_name="_blank")
        except Exception:
            pass


def main(page: ft.Page):
    engine = SciPubsDataEngine()

    aba_atual = "buscador"
    botao_selecionado = "buscador"
    idioma_atual = "English"
    sobre_expandido = False
    
    pagina_atual = 1
    itens_por_pagina = 20
    resultados_totais_atuais = []
    revistas_selecionadas = set()

    def t(key):
        return DIC_TRANSLATE.get(idioma_atual, DIC_TRANSLATE["English"]).get(key, key)

    page.title = t("titulo_pagina")
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = MAIN_BG
    page.padding = 0
    page.spacing = 0

    # Componentes do Buscador de Periódicos
    termo_busca = ft.Ref[ft.TextField]()
    grande_area_dropdown = ft.Ref[ft.Dropdown]()
    base_dados_dropdown = ft.Ref[ft.Dropdown]()
    quartil_jcr_dropdown = ft.Ref[ft.Dropdown]()
    quartil_sjr_dropdown = ft.Ref[ft.Dropdown]()
    ordenar_dropdown = ft.Ref[ft.Dropdown]()
    per_page_dropdown = ft.Ref[ft.Dropdown]()

    # Componentes do Recomendador Inteligente (CONTAINERS VAZIOS)
    rec_titulo = ft.Ref[ft.TextField]()
    rec_resumo = ft.Ref[ft.TextField]()
    rec_gemini_key = ft.Ref[ft.TextField]()
    rec_db_dropdown = ft.Ref[ft.Dropdown]()
    rec_ordem_dropdown = ft.Ref[ft.Dropdown]()
    rec_slider_ctrl = ft.Ref[ft.Slider]()

    ia_icon_src = get_image_src("target_arrow_colored.svg")

    lbl_info_paginacao = ft.Text("", color="#FFFFFF", size=15, weight=ft.FontWeight.BOLD, font_family="Roboto")
    btn_pag_ant = ft.Ref[ft.Button]()
    btn_pag_prox = ft.Ref[ft.Button]()
    row_paginacao_botoes = ft.Row(spacing=6)

    lista_resultados = ft.Column(spacing=14, scroll=ft.ScrollMode.AUTO, expand=True)

    def atualizar_destaque_botoes(selecionado):
        nonlocal botao_selecionado
        botao_selecionado = selecionado

        btn_busca_tab.style.side = ft.BorderSide(3, "#FFFFFF") if botao_selecionado == "buscador" else None
        btn_rec_tab.style.side = ft.BorderSide(3, "#FFFFFF") if botao_selecionado == "recomendador" else None
        btn_doar.style.side = ft.BorderSide(3, "#FFFFFF") if botao_selecionado == "doar" else None
        btn_inscrever.style.side = ft.BorderSide(3, "#FFFFFF") if botao_selecionado == "inscrever" else None
        page.update()

    def abrir_modal_inscricao(e=None):
        atualizar_destaque_botoes("inscrever")

        txt_nome = ft.TextField(label=t("nome"), bgcolor=INPUT_BG, color="#FFFFFF", border_radius=8, hint_style=ft.TextStyle(color=TEXT_MUTED, size=13, font_family="Roboto"))
        txt_email = ft.TextField(label=t("email"), bgcolor=INPUT_BG, color="#FFFFFF", border_radius=8, hint_style=ft.TextStyle(color=TEXT_MUTED, size=13, font_family="Roboto"))

        def fechar_dialog(e=None):
            dialog.open = False
            try:
                page.close(dialog)
            except Exception:
                pass
            page.update()

        dialog = ft.AlertDialog(
            bgcolor=CARD_BG,
            shape=ft.RoundedRectangleBorder(radius=16),
            title=ft.Text(t("sub_modal_tit"), color="#FFFFFF", size=20, weight=ft.FontWeight.BOLD, font_family="Roboto"),
            content=ft.Container(
                width=450,
                content=ft.Column([
                    ft.Text(t("sub_modal_desc"), color=TEXT_MUTED, size=14, font_family="Roboto"),
                    ft.Container(height=8),
                    txt_nome,
                    txt_email
                ], spacing=12, tight=True)
            ),
            actions=[
                ft.Button(t("fechar"), style=ft.ButtonStyle(color="#FFFFFF", bgcolor="#334155"), on_click=fechar_dialog),
                ft.Button(
                    t("inscrever"),
                    style=ft.ButtonStyle(color="#FFFFFF", bgcolor=ACCENT_RED, shape=ft.RoundedRectangleBorder(radius=8), text_style=ft.TextStyle(weight=ft.FontWeight.BOLD, font_family="Roboto")),
                    on_click=fechar_dialog
                )
            ]
        )

        if dialog not in page.overlay:
            page.overlay.append(dialog)
        dialog.open = True
        try:
            page.open(dialog)
        except Exception:
            pass
        page.update()

    def abrir_modal_doacao(e=None):
        atualizar_destaque_botoes("doar")
        abrir_link(page, "https://buymeacoffee.com/scipubs")

    def on_check_changed(e, item_id):
        if e.control.value:
            revistas_selecionadas.add(item_id)
        else:
            revistas_selecionadas.discard(item_id)
        atualizar_rotulos_botoes_download()

    def atualizar_rotulos_botoes_download():
        qtd_sel = len(revistas_selecionadas)
        if qtd_sel > 0:
            btn_export_csv.text = f"{t('baixar_csv')} ({qtd_sel} {t('selecionados')})"
            btn_export_excel.text = f"{t('baixar_excel')} ({qtd_sel} {t('selecionados')})"
        else:
            btn_export_csv.text = t('baixar_csv')
            btn_export_excel.text = t('baixar_excel')
        page.update()

    def exportar_resultados(formato="csv"):
        if revistas_selecionadas:
            export_ids = list(revistas_selecionadas)
        else:
            export_ids = [item.get("issn") if item.get("issn") != "N/A" else item.get("titulo") for item in resultados_totais_atuais[:200]]
            
        if not export_ids:
            return

        if hasattr(engine, 'df_original') and engine.df_original is not None and not engine.df_original.empty:
            cols = list(engine.df_original.columns)
            col_issn = [c for c in cols if 'issn' in str(c).lower()][0] if any('issn' in str(c).lower() for c in cols) else cols[2]
            col_tit = [c for c in cols if ('t' in str(c).lower() and 'tulo' in str(c).lower()) or 'title' in str(c).lower()][0] if any(('t' in str(c).lower() and 'tulo' in str(c).lower()) or 'title' in str(c).lower() for c in cols) else cols[1]

            mask = (engine.df_original[col_issn].astype(str).isin(export_ids)) | (engine.df_original[col_tit].astype(str).isin(export_ids))
            df_export = engine.df_original[mask].copy()
        else:
            df_export = pd.DataFrame([item for item in resultados_totais_atuais if (item.get("issn") in export_ids or item.get("titulo") in export_ids)])

        if df_export.empty and resultados_totais_atuais:
            df_export = pd.DataFrame(resultados_totais_atuais[:200])

        colunas_auxiliares = ["search_text", "S_text", "S_sparse", "S_index", "Score_final", "jif_num", "sjr_num", "h_num", "Prob_aceitacao", "fator_impacto"]
        df_export = df_export.drop(columns=[c for c in colunas_auxiliares if c in df_export.columns], errors="ignore")

        fname = f"scipubs_export_{int(time.time())}.{'csv' if formato == 'csv' else 'xlsx'}"
        fpath = os.path.join(ICONS_DIR, fname)

        if formato == "csv":
            df_export.to_csv(fpath, index=False, encoding="utf-8-sig")
        else:
            df_export.to_excel(fpath, index=False)

        rel_url = f"/{fname}"
        try:
            page.launch_url(rel_url, web_window_name="_blank")
        except Exception:
            pass
        try:
            webbrowser.open(fpath)
        except Exception:
            pass

        msg_template = t("snack_msg")
        snack = ft.SnackBar(
            content=ft.Text(msg_template.format(fname=fname), color="#FFFFFF"),
            bgcolor="#059669"
        )
        page.overlay.append(snack)
        snack.open = True
        page.update()

    btn_export_csv = ft.Button(
        t('baixar_csv'),
        icon=ft.Icons.DOWNLOAD,
        style=ft.ButtonStyle(color="#FFFFFF", bgcolor=ACCENT_GREEN, shape=ft.RoundedRectangleBorder(radius=8)),
        on_click=lambda e: exportar_resultados("csv")
    )

    btn_export_excel = ft.Button(
        t('baixar_excel'),
        icon=ft.Icons.TABLE_VIEW,
        style=ft.ButtonStyle(color="#FFFFFF", bgcolor="#1D6F42", shape=ft.RoundedRectangleBorder(radius=8)),
        on_click=lambda e: exportar_resultados("excel")
    )

    def renderizar_pagina():
        nonlocal pagina_atual, itens_por_pagina
        lista_resultados.controls.clear()
        
        total_items = len(resultados_totais_atuais)
        if total_items == 0:
            lbl_info_paginacao.value = ""
            row_paginacao_botoes.controls.clear()
            lista_resultados.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.SEARCH_OFF, size=54, color=ACCENT_RED),
                        ft.Text(t("sem_resultados"), color="#FFFFFF", size=16, weight=ft.FontWeight.BOLD, font_family="Roboto")
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    alignment=ft.Alignment(0, 0), padding=40
                )
            )
            page.update()
            return

        total_paginas = max(1, (total_items + itens_por_pagina - 1) // itens_por_pagina)
        if pagina_atual > total_paginas:
            pagina_atual = total_paginas
        if pagina_atual < 1:
            pagina_atual = 1

        idx_inicio = (pagina_atual - 1) * itens_por_pagina
        idx_fim = min(idx_inicio + itens_por_pagina, total_items)
        pagina_items = resultados_totais_atuais[idx_inicio:idx_fim]

        fmt_str = t("pagina_fmt")
        lbl_info_paginacao.value = fmt_str.format(
            atual=pagina_atual,
            total=total_paginas,
            total_itens=f"{total_items:,}".replace(",", ".")
        )

        row_paginacao_botoes.controls.clear()
        
        def ir_pagina(p):
            nonlocal pagina_atual
            pagina_atual = p
            renderizar_pagina()

        btn_ant = ft.Button(
            t("pag_anterior"),
            icon=ft.Icons.ARROW_BACK,
            disabled=(pagina_atual == 1),
            style=ft.ButtonStyle(color="#FFFFFF", bgcolor=INPUT_BG if pagina_atual > 1 else "#1E293B"),
            on_click=lambda e: ir_pagina(pagina_atual - 1)
        )

        btn_prox = ft.Button(
            t("pag_proxima"),
            icon=ft.Icons.ARROW_FORWARD,
            disabled=(pagina_atual == total_paginas),
            style=ft.ButtonStyle(color="#FFFFFF", bgcolor=INPUT_BG if pagina_atual < total_paginas else "#1E293B"),
            on_click=lambda e: ir_pagina(pagina_atual + 1)
        )

        row_paginacao_botoes.controls.append(btn_ant)
        
        p_start = max(1, pagina_atual - 2)
        p_end = min(total_paginas, p_start + 4)
        if p_end - p_start < 4:
            p_start = max(1, p_end - 4)

        for p_num in range(p_start, p_end + 1):
            is_active = (p_num == pagina_atual)
            btn_p = ft.Button(
                str(p_num),
                style=ft.ButtonStyle(
                    color="#FFFFFF" if is_active else TEXT_MUTED,
                    bgcolor=ACCENT_RED if is_active else INPUT_BG,
                    shape=ft.RoundedRectangleBorder(radius=6)
                ),
                on_click=lambda e, num=p_num: ir_pagina(num)
            )
            row_paginacao_botoes.controls.append(btn_p)

        row_paginacao_botoes.controls.append(btn_prox)

        for item in pagina_items:
            titulo_p = item.get("titulo", "Sem Título")
            issn = item.get("issn", "N/A")
            item_id = issn if issn != "N/A" else titulo_p

            chk_item = ft.Checkbox(
                value=(item_id in revistas_selecionadas),
                fill_color=ACCENT_RED,
                on_change=lambda e, i_id=item_id: on_check_changed(e, i_id)
            )

            g_area = item.get("grande_area", "-")
            if not g_area or g_area in ["", "nan", "None"]: g_area = t("geral")
            
            area_item = item.get("area", "-")
            if not area_item or area_item in ["", "nan", "None"]: area_item = t("geral")

            cat_item = item.get("categoria", "-")
            if not cat_item or cat_item in ["", "nan", "None"]: cat_item = t("multidisciplinar")

            indexadores = item.get("indexador", t("nao_informado"))
            if not indexadores or str(indexadores).strip() in ["", "nan", "None"]: indexadores = t("nao_informado")

            fator = item.get("jif", "-")
            q_jcr = item.get("quartil_jcr", "-")

            val_sjr = item.get("sjr", "-")
            q_sjr = item.get("quartil_sjr", "-")

            h_idx = item.get("h_index", "-")

            site_url = item.get("homepage", "")
            h5_url = item.get("h5_link", f"https://scholar.google.com/citations?hl=pt-BR&view_op=search_venues&vq={urllib.parse.quote(titulo_p)}&btnG=")
            score = item.get("Score_final", None)
            prob_val = item.get("Prob_aceitacao", None)

            badge_score = None
            badge_prob = None
            if score is not None:
                percentual = min(100, max(5, int(round(score))))
                badge_score = ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.AUTO_AWESOME, color=GOLD_YELLOW, size=14),
                        ft.Text(f"{percentual}% Match Híbrido", color=GOLD_YELLOW, size=12, weight=ft.FontWeight.BOLD, font_family="Roboto")
                    ], spacing=4),
                    bgcolor="#1E1B4B",
                    padding=ft.Padding(8, 4, 8, 4),
                    border_radius=6,
                    border=ft.Border.all(1, GOLD_YELLOW)
                )

            if prob_val is not None:
                badge_prob = ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE, color="#4ADE80", size=14),
                        ft.Text(f"{t('prob_aceitacao')}: {prob_val}%", color="#4ADE80", size=12, weight=ft.FontWeight.BOLD, font_family="Roboto")
                    ], spacing=4),
                    bgcolor="#064E3B",
                    padding=ft.Padding(8, 4, 8, 4),
                    border_radius=6,
                    border=ft.Border.all(1, "#059669")
                )

            title_spans = [
                ft.TextSpan(f"{titulo_p} ", style=ft.TextStyle(font_family="Roboto", size=22, weight=ft.FontWeight.BOLD, color="#FFFFFF")),
                ft.TextSpan(f"(ISSN: {issn})", style=ft.TextStyle(font_family="Roboto", size=22, weight=ft.FontWeight.NORMAL, color="#FFFFFF"))
            ]

            bases_spans = [
                ft.TextSpan(f"{t('bases_lbl')}: ", style=ft.TextStyle(font_family="Roboto", size=16, weight=ft.FontWeight.NORMAL, color="#FFFFFF")),
                ft.TextSpan(str(indexadores), style=ft.TextStyle(font_family="Roboto", size=16, weight=ft.FontWeight.BOLD, color=ACCENT_RED))
            ]

            card = ft.Container(
                bgcolor=CARD_BG,
                border_radius=14,
                padding=18,
                border=ft.Border.all(1, BORDER_DARK),
                content=ft.Column([
                    ft.Row([
                        ft.Row([chk_item, ft.Text(spans=title_spans, overflow=ft.TextOverflow.ELLIPSIS, max_lines=2)], expand=True, spacing=8),
                        ft.Row([
                            badge_score if badge_score else ft.Container(),
                            badge_prob if badge_prob else ft.Container(),
                            ft.Button(
                                t("acesse_site"),
                                icon=ft.Icons.OPEN_IN_NEW,
                                style=ft.ButtonStyle(color="#FFFFFF", bgcolor=ACCENT_BLUE, shape=ft.RoundedRectangleBorder(radius=8)),
                                on_click=lambda e, u=site_url, t_p=titulo_p: abrir_link(page, u, t_p)
                            )
                        ], spacing=8)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),

                    ft.Text(f"{t('grande_area_lbl')}: {g_area}", font_family="Roboto", size=12, weight=ft.FontWeight.NORMAL, color="#FFFFFF"),
                    ft.Text(f"{t('area_lbl')}: {area_item}", font_family="Roboto", size=12, weight=ft.FontWeight.NORMAL, color="#FFFFFF"),
                    ft.Text(f"{t('cat_lbl')}: {cat_item}", font_family="Roboto", size=12, weight=ft.FontWeight.NORMAL, color="#FFFFFF"),
                    ft.Text(spans=bases_spans),

                    ft.Divider(color=BORDER_DARK, height=12),

                    ft.Row([
                        ft.Text(f"JIF: {fator} ({q_jcr})", font_family="Roboto", color=GOLD_YELLOW, size=14, weight=ft.FontWeight.BOLD),
                        ft.Text(f"SJR: {val_sjr} ({q_sjr})", font_family="Roboto", color=GOLD_YELLOW, size=14, weight=ft.FontWeight.BOLD),
                        ft.Text(f"{t('h_lbl')}: {h_idx}", font_family="Roboto", color=GOLD_YELLOW, size=14, weight=ft.FontWeight.BOLD),
                        ft.Button(
                            t("ver_h5"),
                            icon=ft.Icons.TRACK_CHANGES,
                            style=ft.ButtonStyle(color=GOLD_YELLOW, bgcolor=INPUT_BG, shape=ft.RoundedRectangleBorder(radius=8), side=ft.BorderSide(1, GOLD_YELLOW)),
                            on_click=lambda e, u=h5_url, t_p=titulo_p: abrir_link(page, u, t_p)
                        )
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER)
                ], spacing=6)
            )
            lista_resultados.controls.append(card)

        page.update()

    def executar_pesquisa(e=None):
        nonlocal resultados_totais_atuais, pagina_atual, itens_por_pagina

        if per_page_dropdown.current and per_page_dropdown.current.value:
            try:
                itens_por_pagina = int(per_page_dropdown.current.value)
            except Exception:
                itens_por_pagina = 20

        pagina_atual = 1

        if aba_atual == "buscador":
            query = termo_busca.current.value if termo_busca.current else ""
            g_area = grande_area_dropdown.current.value if grande_area_dropdown.current else t("todas")
            b_dados = base_dados_dropdown.current.value if base_dados_dropdown.current else "Todas"
            q_jcr = quartil_jcr_dropdown.current.value if quartil_jcr_dropdown.current else t("todos")
            q_sjr = quartil_sjr_dropdown.current.value if quartil_sjr_dropdown.current else t("todos")
            
            ordem_idx = 0
            if ordenar_dropdown.current and ordenar_dropdown.current.value:
                curr_opts = t("ordem_opts")
                if ordenar_dropdown.current.value in curr_opts:
                    ordem_idx = curr_opts.index(ordenar_dropdown.current.value)

            resultados_totais_atuais = engine.buscar_geral(
                termo=query,
                grande_area=g_area,
                base_dados=b_dados,
                quartil_jcr=q_jcr,
                quartil_sjr=q_sjr,
                ordenacao=ordem_idx,
                limite=1000
            )
        else:
            tit = rec_titulo.current.value if rec_titulo.current else ""
            res = rec_resumo.current.value if rec_resumo.current else ""
            db_sel = rec_db_dropdown.current.value if rec_db_dropdown.current else "Todas"
            limite_sel = int(rec_slider_ctrl.current.value) if rec_slider_ctrl.current else 20

            ordem_rec_idx = 0
            if rec_ordem_dropdown.current and rec_ordem_dropdown.current.value:
                curr_opts = t("ordem_opts")
                if rec_ordem_dropdown.current.value in curr_opts:
                    ordem_rec_idx = curr_opts.index(rec_ordem_dropdown.current.value)

            if not tit.strip() and not res.strip():
                resultados_totais_atuais = []
                renderizar_pagina()
                return

            resultados_totais_atuais = engine.recomendar_manuscrito(titulo=tit, resumo=res, area_filtro=db_sel, ordenacao_idx=ordem_rec_idx, limite=limite_sel)

        renderizar_pagina()

    def alternar_aba(nova_aba):
        nonlocal aba_atual
        aba_atual = nova_aba
        atualizar_destaque_botoes(nova_aba)

        render_responsive_layout()
        executar_pesquisa()

    lbl_indexadores = ft.Text(t("indexadores_tit"), size=12, weight=ft.FontWeight.BOLD, color="#000000", font_family="Roboto")
    lbl_repositorios = ft.Text(t("repositorios_tit"), size=12, weight=ft.FontWeight.BOLD, color="#000000", font_family="Roboto")
    lbl_ia = ft.Text(t("ia_tit"), size=12, weight=ft.FontWeight.BOLD, color="#000000", font_family="Roboto")
    lbl_gov = ft.Text(t("gov_tit"), size=12, weight=ft.FontWeight.BOLD, color="#000000", font_family="Roboto")
    lbl_inst = ft.Text(t("inst_tit"), size=12, weight=ft.FontWeight.BOLD, color="#000000", font_family="Roboto")
    btn_pessoal_txt = ft.Ref[ft.Text]()

    btn_busca_txt = ft.Text(t("busca_cat"), color="#FFFFFF", size=14, weight=ft.FontWeight.BOLD, font_family="Roboto")
    btn_rec_txt = ft.Text(t("busca_ia"), color="#FFFFFF", size=14, weight=ft.FontWeight.BOLD, font_family="Roboto")
    btn_doar_txt = ft.Text(t("doacoes"), color="#000000", size=14, weight=ft.FontWeight.BOLD, font_family="Roboto")
    btn_inscrever_txt = ft.Text(t("inscrever"), color="#FFFFFF", size=14, weight=ft.FontWeight.BOLD, font_family="Roboto")

    btn_busca_tab = ft.Button(
        content=ft.Row([btn_busca_txt], alignment=ft.MainAxisAlignment.CENTER),
        style=ft.ButtonStyle(
            color="#FFFFFF",
            bgcolor=ACCENT_BLUE,
            padding=ft.Padding(16, 14, 16, 14),
            shape=ft.RoundedRectangleBorder(radius=10),
            side=ft.BorderSide(3, "#FFFFFF")
        ),
        expand=True,
        on_click=lambda e: alternar_aba("buscador")
    )

    btn_rec_tab = ft.Button(
        content=ft.Row([
            ft.Image(src=ia_icon_src, width=22, height=22, fit="contain") if ia_icon_src else ft.Icon(ft.Icons.TRACK_CHANGES, size=20, color="#FFFFFF"),
            btn_rec_txt
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=8),
        style=ft.ButtonStyle(
            color="#FFFFFF",
            bgcolor=ACCENT_GREEN,
            padding=ft.Padding(16, 14, 16, 14),
            shape=ft.RoundedRectangleBorder(radius=10)
        ),
        expand=True,
        on_click=lambda e: alternar_aba("recomendador")
    )

    btn_doar = ft.Button(
        content=ft.Row([btn_doar_txt], alignment=ft.MainAxisAlignment.CENTER),
        style=ft.ButtonStyle(color="#000000", bgcolor=ACCENT_YELLOW, padding=ft.Padding(16, 14, 16, 14), shape=ft.RoundedRectangleBorder(radius=10)),
        expand=True,
        on_click=abrir_modal_doacao
    )

    btn_inscrever = ft.Button(
        content=ft.Row([btn_inscrever_txt], alignment=ft.MainAxisAlignment.CENTER),
        style=ft.ButtonStyle(color="#FFFFFF", bgcolor=ACCENT_RED, padding=ft.Padding(16, 14, 16, 14), shape=ft.RoundedRectangleBorder(radius=10)),
        expand=True,
        on_click=abrir_modal_inscricao
    )

    action_buttons_row = ft.Row([btn_busca_tab, btn_rec_tab, btn_doar, btn_inscrever], spacing=10)

    def toggle_sobre(e):
        nonlocal sobre_expandido
        sobre_expandido = not sobre_expandido
        sobre_content.visible = sobre_expandido
        page.update()

    sobre_tit_ctrl = ft.Text(t("sobre_tit"), color="#FFFFFF", size=14, weight=ft.FontWeight.BOLD, font_family="Roboto")

    txt_head = ft.Text(t("sobre_head"), color="#FFFFFF", size=22, weight=ft.FontWeight.BOLD, font_family="Roboto")
    txt_sub = ft.Text(t("sobre_sub"), color="#FFFFFF", size=14, weight=ft.FontWeight.NORMAL, font_family="Roboto")
    txt_what = ft.Text(t("sobre_what"), color="#FFFFFF", size=18, weight=ft.FontWeight.BOLD, font_family="Roboto")

    def make_code_badge(text):
        return ft.Container(
            content=ft.Text(text, color="#4ADE80", size=12, font_family="Consolas, monospace", weight=ft.FontWeight.BOLD),
            bgcolor="#152C22",
            padding=ft.Padding(5, 2, 5, 2),
            border_radius=4,
            border=ft.Border.all(1, "#1E3B2B")
        )

    def build_item1_row():
        return ft.Row([
            ft.Text(t("item1_title"), color="#FFFFFF", size=14, weight=ft.FontWeight.BOLD, font_family="Roboto"),
            ft.Text(t("item1_desc1"), color="#FFFFFF", size=14, font_family="Roboto"),
            make_code_badge('"music education"'),
            ft.Text(t("item1_desc2"), color="#FFFFFF", size=14, font_family="Roboto"),
            make_code_badge("AND"),
            ft.Text(" , ", color="#FFFFFF", size=14, font_family="Roboto"),
            make_code_badge("OR"),
            ft.Text(" , ", color="#FFFFFF", size=14, font_family="Roboto"),
            make_code_badge("NOT"),
            ft.Text(t("item1_desc3"), color="#FFFFFF", size=14, font_family="Roboto"),
            make_code_badge("music AND education NOT medicine"),
            ft.Text(t("item1_desc4"), color="#FFFFFF", size=14, font_family="Roboto")
        ], wrap=True, spacing=2)

    def format_simple_item(title_key, desc_key):
        return ft.Text(spans=[
            ft.TextSpan(t(title_key), style=ft.TextStyle(font_family="Roboto", weight=ft.FontWeight.BOLD, color="#FFFFFF")),
            ft.TextSpan(t(desc_key), style=ft.TextStyle(font_family="Roboto", weight=ft.FontWeight.NORMAL, color="#FFFFFF"))
        ], size=14)

    item1_container = ft.Container(content=build_item1_row())
    item2_ctrl = format_simple_item("item2_title", "item2_desc")
    item3_ctrl = format_simple_item("item3_title", "item3_desc")
    item4_ctrl = format_simple_item("item4_title", "item4_desc")
    item5_ctrl = format_simple_item("item5_title", "item5_desc")

    sobre_content = ft.Container(
        visible=False,
        bgcolor="#0F172A",
        padding=24,
        border_radius=14,
        content=ft.Column([
            txt_head,
            txt_sub,
            ft.Container(height=8),
            txt_what,
            ft.Container(height=6),
            item1_container,
            ft.Container(height=4),
            item2_ctrl,
            ft.Container(height=4),
            item3_ctrl,
            ft.Container(height=4),
            item4_ctrl,
            ft.Container(height=4),
            item5_ctrl
        ], spacing=10)
    )

    sobre_expander = ft.Container(
        bgcolor="#0F172A",
        border_radius=14,
        padding=14,
        border=ft.Border.all(1, BORDER_DARK),
        on_click=toggle_sobre,
        content=ft.Column([
            ft.Row([
                ft.Row([
                    ft.Icon(ft.Icons.KEYBOARD_ARROW_DOWN, color="#FFFFFF", size=16),
                    sobre_tit_ctrl
                ], spacing=6),
                ft.Container()
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            sobre_content
        ])
    )

    btn_fale_txt = ft.Text(t("fale_conosco"), color="#FFFFFF", size=15, weight=ft.FontWeight.BOLD, font_family="Roboto")
    
    btn_fale = ft.Container(
        content=ft.Row([
            ft.Icon(ft.Icons.EMAIL, color="#FFFFFF", size=18),
            btn_fale_txt
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=8),
        bgcolor=ACCENT_RED,
        padding=ft.Padding(12, 12, 12, 12),
        border_radius=8,
        width=240,
        on_click=lambda e: abrir_link(page, "mailto:support@scipubs.com"),
        ink=True
    )

    btn_win = ft.Button(
        t("baixar_win"),
        style=ft.ButtonStyle(color="#FFFFFF", bgcolor=ACCENT_RED, shape=ft.RoundedRectangleBorder(radius=8), text_style=ft.TextStyle(size=14, weight=ft.FontWeight.BOLD, font_family="Roboto")),
        width=240,
        on_click=lambda e: abrir_link(page, "https://drive.google.com/")
    )

    nav_tit_ctrl = ft.Text(t("nav_tit"), size=22, weight=ft.FontWeight.BOLD, color="#000000", font_family="Roboto")
    lbl_copyright_tit = ft.Text(t("copyright_tit"), size=11, weight=ft.FontWeight.BOLD, color="#000000", font_family="Roboto")
    lbl_copyright_desc = ft.Text(t("copyright_desc"), size=11, color=TEXT_DARK, font_family="Roboto")

    btn_capes_cat = ft.Ref[ft.Text]()
    btn_lattes = ft.Ref[ft.Text]()
    btn_periodicos_capes = ft.Ref[ft.Text]()
    btn_musica_ufop = ft.Ref[ft.Text]()

    def mudar_idioma(novo_idioma):
        nonlocal idioma_atual
        idioma_atual = novo_idioma
        page.title = t("titulo_pagina")

        btn_busca_txt.value = t("busca_cat")
        btn_rec_txt.value = t("busca_ia")
        btn_doar_txt.value = t("doacoes")
        btn_inscrever_txt.value = t("inscrever")

        btn_fale_txt.value = t("fale_conosco")
        btn_win.text = t("baixar_win")

        btn_busca_tab.update()
        btn_rec_tab.update()
        btn_doar.update()
        btn_inscrever.update()
        btn_win.update()

        sobre_tit_ctrl.value = t("sobre_tit")
        txt_head.value = t("sobre_head")
        txt_sub.value = t("sobre_sub")
        txt_what.value = t("sobre_what")
        
        item1_container.content = build_item1_row()
        item2_ctrl.spans[0].text = t("item2_title")
        item2_ctrl.spans[1].text = t("item2_desc")
        item3_ctrl.spans[0].text = t("item3_title")
        item3_ctrl.spans[1].text = t("item3_desc")
        item4_ctrl.spans[0].text = t("item4_title")
        item4_ctrl.spans[1].text = t("item4_desc")
        item5_ctrl.spans[0].text = t("item5_title")
        item5_ctrl.spans[1].text = t("item5_desc")

        nav_tit_ctrl.value = t("nav_tit")
        lbl_indexadores.value = t("indexadores_tit")
        lbl_repositorios.value = t("repositorios_tit")
        lbl_ia.value = t("ia_tit")
        lbl_gov.value = t("gov_tit")
        lbl_inst.value = t("inst_tit")

        if btn_pessoal_txt.current: btn_pessoal_txt.current.value = t("pessoal_lbl")
        if btn_capes_cat.current: btn_capes_cat.current.value = t("cat_capes_lbl")
        if btn_lattes.current: btn_lattes.current.value = t("lattes_lbl")
        if btn_periodicos_capes.current: btn_periodicos_capes.current.value = t("periodicos_capes_lbl")
        if btn_musica_ufop.current: btn_musica_ufop.current.value = t("musica_ufop_lbl")

        lbl_copyright_tit.value = t("copyright_tit")
        lbl_copyright_desc.value = t("copyright_desc")

        logo_src = get_image_src("logo_en.png" if novo_idioma == "English" else ("logo_es.png" if novo_idioma == "Español" else "logo.png"))
        if logo_src:
            sidebar_logo_ctrl.src = logo_src

        banner_src = get_banner_src(novo_idioma)
        if banner_src:
            hero_banner_img.src = banner_src

        atualizar_rotulos_botoes_download()
        render_responsive_layout()
        executar_pesquisa()

    logo_src = get_image_src("logo_en.png")
    sidebar_logo_ctrl = ft.Image(src=logo_src, width=200, fit="contain") if logo_src else ft.Text("SCIPUBS", size=24, weight=ft.FontWeight.BOLD, color=TEXT_DARK, font_family="Roboto")

    def criar_btn_link(texto_key, url, icon_filename=None, default_icon=ft.Icons.LANGUAGE, ref_ctrl=None, is_pessoal=False):
        txt_display = t(texto_key) if texto_key in DIC_TRANSLATE["English"] else texto_key
        text_ctrl = ft.Text(txt_display, ref=ref_ctrl, size=14, weight=ft.FontWeight.W_600 if is_pessoal else ft.FontWeight.W_500, color="#004B87", font_family="Roboto")

        icon_src = get_image_src(icon_filename) if icon_filename else None
        icon_widget = None

        if is_pessoal:
            icon_widget = ft.Icon(ft.Icons.PERSON, size=18, color="#004B87")
            content_row = ft.Row([
                icon_widget,
                text_ctrl
            ], spacing=10, alignment=ft.MainAxisAlignment.START)
        else:
            if icon_src:
                icon_widget = ft.Image(
                    src=icon_src,
                    width=20,
                    height=20,
                    fit="contain",
                    border_radius=2,
                    error_content=ft.Icon(default_icon, size=18, color="#004B87")
                )
            else:
                icon_widget = ft.Icon(default_icon, size=18, color="#004B87")

            content_row = ft.Row([icon_widget, text_ctrl], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER)

        c = ft.Container(
            content=content_row,
            padding=ft.Padding(10, 8, 10, 8),
            bgcolor="#FFFFFF",
            border_radius=6,
            border=ft.Border.all(1, "#004B87"),
            width=240,
            on_click=lambda e: abrir_link(page, url),
            ink=True
        )

        def on_hover(e):
            if e.data == "true":
                c.bgcolor = ACCENT_RED
                c.border = ft.Border.all(1, ACCENT_RED)
                text_ctrl.color = "#FFFFFF"
                if icon_widget and isinstance(icon_widget, ft.Icon):
                    icon_widget.color = "#FFFFFF"
            else:
                c.bgcolor = "#FFFFFF"
                c.border = ft.Border.all(1, "#004B87")
                text_ctrl.color = "#004B87"
                if icon_widget and isinstance(icon_widget, ft.Icon):
                    icon_widget.color = "#004B87"
            page.update()

        c.on_hover = on_hover
        return c

    sidebar_container = ft.Container(
        width=280,
        bgcolor=SIDEBAR_BG,
        padding=16,
        border=ft.Border(right=ft.BorderSide(1, "#E2E8F0")),
        content=ft.Column([
            ft.Row([
                ft.Container(),
                ft.Icon(ft.Icons.KEYBOARD_DOUBLE_ARROW_LEFT, color="#CBD5E1", size=18)
            ], alignment=ft.MainAxisAlignment.END),

            ft.Container(content=sidebar_logo_ctrl, alignment=ft.Alignment(0, 0), padding=ft.Padding(0, 5, 0, 10)),
            
            ft.Row([
                ft.Icon(ft.Icons.LANGUAGE, size=16, color="#2563EB"),
                ft.Text("Language / Idioma:", size=13, color="#1E3A8A", weight=ft.FontWeight.W_600, font_family="Roboto")
            ], spacing=6),
            
            ft.Dropdown(
                options=[
                    ft.dropdown.Option("English"),
                    ft.dropdown.Option("Português"),
                    ft.dropdown.Option("Español")
                ],
                value="English",
                width=240,
                fill_color=SIDEBAR_BG,
                bgcolor=CARD_BG,
                color="#000000",
                border_color="#CBD5E1",
                border_radius=8,
                text_size=14,
                on_select=lambda e: mudar_idioma(e.control.value)
            ),
            
            ft.Container(height=4),
            btn_fale,
            ft.Container(height=6),
            nav_tit_ctrl,
            ft.Divider(color="#CBD5E1", height=15),

            lbl_indexadores,
            criar_btn_link("Web of Science", "https://access.clarivate.com/login?app=wos&alternative=true&goto=https:%2F%2Fwww.webofknowledge.com", "wos.png", ft.Icons.PUBLIC),
            criar_btn_link("Scopus", "https://www.scopus.com/pages/home?display=basic#basic", "scopus.png", ft.Icons.SEARCH),
            criar_btn_link("PubMed", "https://pubmed.ncbi.nlm.nih.gov/", "pubmed.png", ft.Icons.LOCAL_HOSPITAL),
            criar_btn_link("Scielo BR", "https://www.scielo.br/", "scielo.png", ft.Icons.MENU_BOOK),
            criar_btn_link("Educ@", "http://educa.fcc.org.br/cgi-bin/wxis.exe/iah/?IsisScript=iah/iah.xis&base=title&fmt=iso.pft&lang=p", "educa.jpg", ft.Icons.SCHOOL),
            criar_btn_link("JSTOR", "https://www.jstor.org/", "jstor.svg", ft.Icons.BOOKMARK),
            criar_btn_link("Latindex", "https://www.latindex.org/latindex/", "latindex.png", ft.Icons.LANGUAGE),

            ft.Divider(color="#CBD5E1", height=15),
            lbl_repositorios,
            criar_btn_link("ERIC", "https://eric.ed.gov/", "eric.png", ft.Icons.FOLDER_SPECIAL),
            criar_btn_link("BASE", "https://api.base-search.net/", "base.png", ft.Icons.STORAGE),
            criar_btn_link("DOAJ", "https://doaj.org/", "doaj.png", ft.Icons.OPEN_IN_BROWSER),
            criar_btn_link("cat_capes_lbl", "https://catalogodeteses.capes.gov.br/catalogo-teses/#!/", "capes_cat.png", ft.Icons.ACCOUNT_BALANCE, ref_ctrl=btn_capes_cat),

            ft.Divider(color="#CBD5E1", height=15),
            lbl_ia,
            criar_btn_link("ScopusAI", "https://www.scopus.com/pages/home#scopus-ai", "scopus_ai.png", ft.Icons.AUTO_AWESOME),
            criar_btn_link("LeapSpace", "https://researcher.elsevier.com/", "leapspace.jpg", ft.Icons.EXPLORE),
            criar_btn_link("ResearchRabbit", "https://www.researchrabbit.ai/", "researchrabbit.jpg", ft.Icons.PSYCHOLOGY),
            criar_btn_link("Perplexity", "https://www.perplexity.ai/", "perplexity.jpg", ft.Icons.LIGHTBULB),
            criar_btn_link("ConnectedPapers", "https://www.connectedpapers.com/", "connectedpapers.jpg", ft.Icons.HUB),
            criar_btn_link("Consensus", "https://consensus.app/", "consensus.png", ft.Icons.CHECK_CIRCLE_OUTLINE),
            criar_btn_link("SciSpace", "https://scispace.com/", "scispace.png", ft.Icons.SATELLITE_ALT),
            criar_btn_link("Elicit", "https://elicit.com/", "elicit.png", ft.Icons.FILTER_ALT),
            criar_btn_link("Logically", "https://logically.app/", "logically.png", ft.Icons.ANALYTICS),
            criar_btn_link("PubMed.AI", "https://www.pubmed.ai/home", "pubmed_ai.png", ft.Icons.MEDICATION),

            ft.Divider(color="#CBD5E1", height=15),
            lbl_gov,
            criar_btn_link("CNPq", "https://cnpq.br/", "cnpq.png", ft.Icons.ASSURED_WORKLOAD),
            criar_btn_link("CAPES", "https://www.gov.br/capes/pt-br", "capes.png", ft.Icons.ACCOUNT_BALANCE),
            criar_btn_link("lattes_lbl", "https://lattes.cnpq.br/", "lattes.png", ft.Icons.ARTICLE, ref_ctrl=btn_lattes),
            criar_btn_link("periodicos_capes_lbl", "https://www.periodicos.capes.gov.br/", "periodicos_capes.png", ft.Icons.LIBRARY_BOOKS, ref_ctrl=btn_periodicos_capes),

            ft.Divider(color="#CBD5E1", height=15),
            lbl_inst,
            criar_btn_link("UFOP", "https://www.ufop.br", "ufop.png", ft.Icons.SCHOOL),
            criar_btn_link("PPGE-UFOP", "https://www.posedu.ufop.br", "ppge.png", ft.Icons.CAST_FOR_EDUCATION),
            criar_btn_link("musica_ufop_lbl", "https://www.musica.ufop.br", "musica_ufop.png", ft.Icons.MUSIC_NOTE, ref_ctrl=btn_musica_ufop),
            criar_btn_link("pessoal_lbl", "https://professor.ufop.br/joaoquadros", is_pessoal=True, ref_ctrl=btn_pessoal_txt),

            ft.Divider(color="#CBD5E1", height=20),
            btn_win,

            ft.Divider(color="#CBD5E1", height=15),
            lbl_copyright_tit,
            lbl_copyright_desc

        ], spacing=8, scroll=ft.ScrollMode.AUTO)
    )

    banner_init_src = get_banner_src("English")
    hero_banner_img = ft.Image(
        src=banner_init_src,
        fit="fill",
        aspect_ratio=1024 / 323
    )

    hero_card = ft.Container(
        bgcolor="#040A1A",
        border_radius=14,
        padding=0,
        alignment=ft.Alignment(0, 0),
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        border=ft.Border(
            left=ft.BorderSide(6, ACCENT_RED),
            top=ft.BorderSide(1, BORDER_DARK),
            right=ft.BorderSide(1, BORDER_DARK),
            bottom=ft.BorderSide(1, BORDER_DARK)
        ),
        content=hero_banner_img
    )

    form_container = ft.Container(padding=ft.Padding(0, 10, 0, 10))

    def make_sidebar_expander(title_text, content_widget, width=380, title_size=16):
        expanded = [False]
        body = ft.Container(visible=False, content=content_widget, padding=12, bgcolor=INPUT_BG, border_radius=8, width=width)
        header = ft.Container(
            content=ft.Row([
                ft.Text(title_text, color="#FFFFFF", size=title_size, weight=ft.FontWeight.BOLD, font_family="Roboto"),
                ft.Icon(ft.Icons.KEYBOARD_ARROW_RIGHT, color="#FFFFFF", size=18)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            bgcolor=INPUT_BG,
            padding=ft.Padding(12, 10, 12, 10),
            border_radius=8,
            width=width,
            border=ft.Border.all(1, "#334155"),
            on_click=lambda e: toggle_exp()
        )
        def toggle_exp():
            expanded[0] = not expanded[0]
            body.visible = expanded[0]
            header.content.controls[1].name = ft.Icons.KEYBOARD_ARROW_DOWN if expanded[0] else ft.Icons.KEYBOARD_ARROW_RIGHT
            page.update()
        return ft.Column([header, body], spacing=4)

    def render_responsive_layout(e=None):
        is_mobile = page.width < 900
        curr_areas = t("areas")
        quartil_options = [t("todos"), "Q1", "Q2", "Q3", "Q4"]
        ordem_options = t("ordem_opts")
        per_page_options = ["10", "20", "50", "200"]

        if aba_atual == "buscador":
            search_field = ft.TextField(
                ref=termo_busca,
                hint_text=t("placeholder_busca"),
                prefix_icon=ft.Icons.SEARCH,
                bgcolor=INPUT_BG,
                border_color=BORDER_DARK,
                color="#FFFFFF",
                hint_style=ft.TextStyle(color=TEXT_MUTED, size=13, font_family="Roboto"),
                border_radius=10,
                on_submit=executar_pesquisa,
                expand=True
            )

            g_area_select = ft.Dropdown(
                ref=grande_area_dropdown,
                options=[ft.dropdown.Option(a) for a in curr_areas],
                value=curr_areas[0],
                label=t("grande_area_lbl"),
                bgcolor=INPUT_BG,
                border_color=BORDER_DARK,
                color="#FFFFFF",
                border_radius=10,
                on_select=executar_pesquisa,
                expand=True
            )

            db_select = ft.Dropdown(
                ref=base_dados_dropdown,
                options=[ft.dropdown.Option(db) for db in BASES_DADOS_OPCOES],
                value=BASES_DADOS_OPCOES[0],
                label=t("bases_lbl"),
                bgcolor=INPUT_BG,
                border_color=BORDER_DARK,
                color="#FFFFFF",
                border_radius=10,
                on_select=executar_pesquisa,
                expand=True
            )

            jcr_select = ft.Dropdown(
                ref=quartil_jcr_dropdown,
                options=[ft.dropdown.Option(q) for q in quartil_options],
                value=quartil_options[0],
                label=t("quartil_jcr_lbl"),
                bgcolor=INPUT_BG,
                border_color=BORDER_DARK,
                color="#FFFFFF",
                border_radius=10,
                on_select=executar_pesquisa,
                expand=True
            )

            sjr_select = ft.Dropdown(
                ref=quartil_sjr_dropdown,
                options=[ft.dropdown.Option(q) for q in quartil_options],
                value=quartil_options[0],
                label=t("quartil_sjr_lbl"),
                bgcolor=INPUT_BG,
                border_color=BORDER_DARK,
                color="#FFFFFF",
                border_radius=10,
                on_select=executar_pesquisa,
                expand=True
            )

            ordem_select = ft.Dropdown(
                ref=ordenar_dropdown,
                options=[ft.dropdown.Option(o) for o in ordem_options],
                value=ordem_options[0],
                label=t("ordenar_lbl"),
                bgcolor=INPUT_BG,
                border_color=BORDER_DARK,
                color="#FFFFFF",
                border_radius=10,
                on_select=executar_pesquisa,
                expand=True
            )

            per_page_select = ft.Dropdown(
                ref=per_page_dropdown,
                options=[ft.dropdown.Option(pp) for pp in per_page_options],
                value=str(itens_por_pagina),
                label=t("itens_pag_lbl"),
                bgcolor=INPUT_BG,
                border_color=BORDER_DARK,
                color="#FFFFFF",
                border_radius=10,
                width=150,
                on_select=executar_pesquisa
            )

            search_btn = ft.Button(
                t("pesquisar"),
                icon=ft.Icons.ARROW_FORWARD,
                style=ft.ButtonStyle(color="#FFFFFF", bgcolor=ACCENT_BLUE, padding=ft.Padding(24, 16, 24, 16), shape=ft.RoundedRectangleBorder(radius=10)),
                on_click=executar_pesquisa
            )

            form_container.content = ft.Column([
                ft.Text(t("cat_tit"), size=22, weight=ft.FontWeight.BOLD, color="#FFFFFF", font_family="Roboto"),
                ft.Row([search_field, search_btn], spacing=12),
                ft.Row([g_area_select, db_select, jcr_select], spacing=12),
                ft.Row([sjr_select, ordem_select, per_page_select], spacing=12)
            ], spacing=12)

        else:
            RIGHT_COL_WIDTH = 380

            txt_titulo = ft.TextField(
                ref=rec_titulo,
                hint_text="",
                value="",
                bgcolor=INPUT_BG,
                border_color=BORDER_DARK,
                color="#FFFFFF",
                border_radius=10,
                height=50,
                expand=True,
                hint_style=ft.TextStyle(color=TEXT_MUTED, size=13, font_family="Roboto")
            )

            txt_resumo = ft.TextField(
                ref=rec_resumo,
                hint_text="",
                value="",
                bgcolor=INPUT_BG,
                border_color=BORDER_DARK,
                color="#FFFFFF",
                border_radius=10,
                multiline=True,
                min_lines=10,
                max_lines=14,
                height=260,
                expand=True,
                hint_style=ft.TextStyle(color=TEXT_MUTED, size=13, font_family="Roboto")
            )

            btn_calcular_rec = ft.Button(
                t("ia_btn_gerar"),
                style=ft.ButtonStyle(color="#FFFFFF", bgcolor=ACCENT_RED, padding=ft.Padding(22, 16, 22, 16), shape=ft.RoundedRectangleBorder(radius=10)),
                on_click=executar_pesquisa
            )

            left_col = ft.Column([
                ft.Text(t("ia_titulo"), color="#FFFFFF", size=24, weight=ft.FontWeight.BOLD, font_family="Roboto"),
                ft.Text(t("ia_subtitulo"), color=TEXT_MUTED, size=13, italic=True, font_family="Roboto"),
                ft.Container(height=6),
                ft.Text(t("ia_campo_titulo"), color="#FFFFFF", size=14, weight=ft.FontWeight.BOLD, font_family="Roboto"),
                ft.Row([txt_titulo]),
                ft.Container(height=4),
                ft.Text(t("ia_campo_resumo"), color="#FFFFFF", size=14, weight=ft.FontWeight.BOLD, font_family="Roboto"),
                ft.Row([txt_resumo]),
                ft.Container(height=10),
                btn_calcular_rec
            ], expand=True, spacing=6)

            txt_key = ft.TextField(
                ref=rec_gemini_key,
                hint_text=t("ia_gemini_hint"),
                bgcolor=INPUT_BG,
                border_color=BORDER_DARK,
                color="#FFFFFF",
                password=True,
                can_reveal_password=True,
                border_radius=10,
                width=RIGHT_COL_WIDTH,
                hint_style=ft.TextStyle(color="#FFFFFF", size=12, font_family="Roboto")
            )

            badge_gemini = ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.KEY, color="#22C55E", size=16),
                    ft.Text(t("ia_gemini_status"), color="#22C55E", size=12, weight=ft.FontWeight.BOLD, font_family="Roboto")
                ], spacing=8),
                bgcolor="#14532D",
                padding=ft.Padding(12, 10, 12, 10),
                border_radius=8,
                width=RIGHT_COL_WIDTH,
                border=ft.Border.all(1, "#15803D")
            )

            exp1_list = t("exp1_items")
            exp1_content = ft.Column([
                ft.Text(f"{idx+1}. {item}", color="#FFFFFF", size=12, font_family="Roboto", weight=ft.FontWeight.NORMAL)
                for idx, item in enumerate(exp1_list)
            ], spacing=6)

            exp2_list = t("exp2_items")
            exp2_content = ft.Column([
                ft.Text(f"{idx+1}. {item}", color="#FFFFFF", size=12, font_family="Roboto", weight=ft.FontWeight.NORMAL)
                for idx, item in enumerate(exp2_list)
            ], spacing=6)

            exp1_widget = make_sidebar_expander(t("about_modes_tit"), exp1_content, width=RIGHT_COL_WIDTH, title_size=16)
            exp2_widget = make_sidebar_expander(t("how_gemini_tit"), exp2_content, width=RIGHT_COL_WIDTH, title_size=16)

            rec_db_dropdown_ctrl = ft.Dropdown(
                ref=rec_db_dropdown,
                options=[ft.dropdown.Option(db) for db in BASES_DADOS_OPCOES],
                value=BASES_DADOS_OPCOES[0],
                bgcolor=INPUT_BG,
                border_color=BORDER_DARK,
                color="#FFFFFF",
                border_radius=10,
                width=RIGHT_COL_WIDTH,
                text_size=12,
                on_select=executar_pesquisa
            )

            rec_ordem_opts = t("ordem_opts")
            rec_ordem_dropdown_ctrl = ft.Dropdown(
                ref=rec_ordem_dropdown,
                options=[ft.dropdown.Option(o) for o in rec_ordem_opts],
                value=rec_ordem_opts[0],
                bgcolor=INPUT_BG,
                border_color=BORDER_DARK,
                color="#FFFFFF",
                border_radius=10,
                width=RIGHT_COL_WIDTH,
                text_size=12,
                on_select=executar_pesquisa
            )

            def on_slider_change(e):
                val = int(e.control.value)
                lbl_slider.value = str(val)
                lbl_slider.update()

            lbl_slider = ft.Text("20", color=ACCENT_RED, size=14, weight=ft.FontWeight.BOLD, font_family="Roboto")
            rec_slider = ft.Slider(
                ref=rec_slider_ctrl,
                min=1,
                max=20,
                divisions=19,
                value=20,
                active_color=ACCENT_RED,
                on_change=on_slider_change
            )

            right_col = ft.Column([
                ft.Text(t("ai_engine_tit"), color="#FFFFFF", size=18, weight=ft.FontWeight.BOLD, font_family="Roboto"),
                ft.Text(t("ai_engine_sub"), color=TEXT_MUTED, size=12, italic=True, font_family="Roboto"),
                ft.Container(height=4),
                ft.Text(t("ia_gemini_key"), color="#FFFFFF", size=18, weight=ft.FontWeight.BOLD, font_family="Roboto"),
                txt_key,
                badge_gemini,
                ft.Container(height=4),
                exp1_widget,
                exp2_widget,
                ft.Container(height=8),
                ft.Text(t("refine_targets"), color="#FFFFFF", size=18, weight=ft.FontWeight.BOLD, font_family="Roboto"),
                rec_db_dropdown_ctrl,
                ft.Container(height=4),
                ft.Text(t("ordenar_lbl"), color="#FFFFFF", size=18, weight=ft.FontWeight.BOLD, font_family="Roboto"),
                rec_ordem_dropdown_ctrl,
                ft.Container(height=4),
                ft.Row([
                    ft.Text(t("num_recs_lbl"), color="#FFFFFF", size=18, weight=ft.FontWeight.BOLD, font_family="Roboto", expand=True),
                    lbl_slider
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(content=rec_slider, width=RIGHT_COL_WIDTH)
            ], width=RIGHT_COL_WIDTH if not is_mobile else None, spacing=8)

            if is_mobile:
                form_container.content = ft.Column([left_col, right_col], spacing=20)
            else:
                form_container.content = ft.Row([left_col, right_col], spacing=24, vertical_alignment=ft.CrossAxisAlignment.START)

        page.update()

    page.on_resize = render_responsive_layout

    top_results_bar = ft.Row([
        lbl_info_paginacao,
        row_paginacao_botoes
    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER)

    bottom_export_row = ft.Row([
        btn_export_csv,
        btn_export_excel
    ], alignment=ft.MainAxisAlignment.END, spacing=12)

    main_content_area = ft.Container(
        expand=True,
        bgcolor=MAIN_BG,
        padding=24,
        content=ft.Column([
            hero_card,
            sobre_expander,
            action_buttons_row,
            form_container,
            top_results_bar,
            ft.Container(content=lista_resultados, expand=True),
            ft.Divider(color=BORDER_DARK, height=20),
            bottom_export_row
        ], spacing=16, scroll=ft.ScrollMode.AUTO)
    )

    global_layout = ft.Row([
        sidebar_container,
        main_content_area
    ], expand=True, spacing=0)

    page.add(global_layout)

    render_responsive_layout()
    executar_pesquisa()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    host = os.environ.get("HOST", "0.0.0.0")
    ft.app(main, assets_dir=ICONS_DIR, host=host, port=port, view=ft.AppView.WEB_BROWSER)

# DEPLOY_VER = 2026_07_31_v3

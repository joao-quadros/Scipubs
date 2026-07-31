import os
import re
import pickle
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Configurações de caminhos
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DADOS_CSV_PATH = os.path.join(BASE_DIR, "dados.csv")

def _get_cache_path():
    """Gera caminho de cache com hash do CSV para invalidar quando o CSV mudar."""
    import hashlib
    cache_dir = os.path.join(BASE_DIR, "data")
    os.makedirs(cache_dir, exist_ok=True)
    
    # Calcula hash do CSV
    csv_hash = ""
    try:
        with open(DADOS_CSV_PATH, "rb") as f:
            csv_hash = hashlib.md5(f.read()).hexdigest()[:8]
    except Exception:
        pass
    
    return os.path.join(cache_dir, f"aims_scope_minilm_vectors_{csv_hash}.pkl")

EMBEDDINGS_CACHE_PATH = _get_cache_path()
MODEL_NAME = "all-MiniLM-L6-v2"

def safe_float(val):
    """Converte um valor de forma segura para float, tratando nulos e formatos de string."""
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
    """Mapeia o maior valor individual de indexador para um periódico conforme as regras atualizadas."""
    if pd.isna(indexer_str) or not isinstance(indexer_str, str) or not indexer_str.strip():
        return 0.0
    
    # Tokeniza exatamente por delimitadores comuns (vírgula, ponto-e-vírgula, hífen, espaço)
    tokens = [t.strip() for t in re.split(r'[,;\-\s]+', indexer_str.lower()) if t.strip()]
    scores = [0.0]
    
    # Web of Science - SCIE: 1.0
    if "scie" in tokens:
        scores.append(1.0)
    # Web of Science - SSCI: 1.0
    if "ssci" in tokens:
        scores.append(1.0)
    # Scopus: 0.8
    if "scopus" in tokens:
        scores.append(0.8)
    # Web of Science - ACHI / AHCI: 0.7
    if "ahci" in tokens or "achi" in tokens:
        scores.append(0.7)
    # SciELO: 0.6
    if "scielo" in tokens:
        scores.append(0.6)
    # Web of Science - ESCI: 0.5
    if "esci" in tokens:
        scores.append(0.5)
    # Educ@: 0.4
    if "educ@" in tokens or "educa" in tokens:
        scores.append(0.4)
        
    return max(scores)

def identificar_grandes_areas(titulo, resumo):
    """Identifica a(s) Grande(s) Área(s) do artigo com base em termos temáticos."""
    text = f"{titulo} {resumo}".lower()
    
    scores = {
        "Linguística, Letras e Artes": 0,
        "Ciências Humanas": 0,
        "Ciências Sociais Aplicadas": 0,
        "Ciências da Saúde": 0,
        "Ciências Biológicas": 0,
        "Ciências Exatas e da Terra": 0,
        "Engenharias": 0,
        "Ciências Agrárias": 0
    }
    
    art_keywords = ["música", "music", "arte", "art", "teatro", "dança", "cinema", "filologia", "literatura", "linguagem", "linguística", "linguistics", "letras", "poesia", "estética"]
    hum_keywords = ["educação", "education", "ensino", "pedagogia", "didática", "história", "history", "geografia", "psicologia", "psychology", "sociologia", "antropologia", "teologia", "filosofia", "humanização", "freire", "escola", "estudantes", "alunos"]
    soc_keywords = ["direito", "law", "administração", "management", "economia", "economics", "contabilidade", "jornalismo", "comunicação", "arquitetura", "urbanismo", "turismo", "políticas públicas"]
    health_keywords = ["saúde", "health", "médica", "medicine", "clínica", "hospital", "paciente", "doença", "tratamento", "terapia", "enfermagem", "farmácia", "odontologia", "nutrição", "nefrologia", "diálise", "transplante"]
    bio_keywords = ["biologia", "biology", "genética", "genetics", "proteína", "célula", "cell", "dna", "rna", "evolução", "espécie", "botânica", "zoologia", "fisiologia", "veterinária"]
    exact_keywords = ["matemática", "physics", "física", "química", "chemistry", "computação", "computer", "software", "algoritmo", "dados", "geologia", "astronomia", "estatística"]
    eng_keywords = ["engenharia", "engineering", "tecnologia", "sistema", "materiais", "infraestrutura", "mecânica", "elétrica", "civil"]
    agri_keywords = ["agricultura", "agronomia", "florestal", "agropecuária", "veterinária", "zootecnia", "solo", "cultivo"]
    
    for kw in art_keywords:
        if kw in text:
            scores["Linguística, Letras e Artes"] += 2
    for kw in hum_keywords:
        if kw in text:
            scores["Ciências Humanas"] += 2
    for kw in soc_keywords:
        if kw in text:
            scores["Ciências Sociais Aplicadas"] += 1
    for kw in health_keywords:
        if kw in text:
            scores["Ciências da Saúde"] += 1
    for kw in bio_keywords:
        if kw in text:
            scores["Ciências Biológicas"] += 1
    for kw in exact_keywords:
        if kw in text:
            scores["Ciências Exatas e da Terra"] += 1
    for kw in eng_keywords:
        if kw in text:
            scores["Engenharias"] += 1
    for kw in agri_keywords:
        if kw in text:
            scores["Ciências Agrárias"] += 1
            
    max_score = max(scores.values())
    if max_score == 0:
        return ["Ciências Humanas"]  # Fallback padrão
        
    # Retorna todas as áreas que empataram ou ficaram muito próximas do topo (tolerância de 2 pontos / 1 palavra-chave)
    selected_areas = [area for area, sc in scores.items() if sc >= max_score - 2 and sc > 0]
    return selected_areas

def carregar_e_normalizar_base():
    """Carrega dados.csv e normaliza as colunas necessárias."""
    if not os.path.exists(DADOS_CSV_PATH):
        raise FileNotFoundError(f"Base de dados não encontrada em: {DADOS_CSV_PATH}")
        
    # Detecta o separador automaticamente
    with open(DADOS_CSV_PATH, "r", encoding="utf-8-sig", errors="ignore") as f:
        first_line = f.readline()
    sep = ";" if first_line.count(";") >= first_line.count(",") else ","
    
    df = pd.read_csv(DADOS_CSV_PATH, sep=sep, encoding="utf-8-sig", low_memory=False, on_bad_lines="skip")
    df.columns = df.columns.str.replace("\ufeff", "", regex=False)
    df.columns = [c.strip() for c in df.columns]
    
    # Normalização de nomes de colunas
    rename_map = {}
    for col in df.columns:
        col_lower = col.lower()
        if "título da revista" in col_lower or "ttulo da revista" in col_lower or "titulo da revista" in col_lower or col_lower == "title":
            rename_map[col] = "titulo_revista"
        elif col_lower == "aims and scope" or col_lower == "aims & scope" or col_lower == "escopo":
            rename_map[col] = "aims_scope"
        elif col_lower == "indexador":
            rename_map[col] = "indexador"
        elif col_lower == "jif":
            rename_map[col] = "jif"
        elif col_lower == "issn":
            rename_map[col] = "issn"
        elif col_lower == "homepage":
            rename_map[col] = "homepage"
        elif "quartil jcr" in col_lower or "jcr quartil" in col_lower or "jcr quartile" in col_lower:
            rename_map[col] = "quartil_jcr"
        elif "sjr best quartile" in col_lower or "sjr quartile" in col_lower:
            rename_map[col] = "sjr_quartile"
        elif "index-h" in col_lower or "h-index" in col_lower or "h index" in col_lower:
            rename_map[col] = "h_index"
        elif "index-h5" in col_lower or "h5" in col_lower:
            rename_map[col] = "h5_link"
        elif "grande área" in col_lower or "grande area" in col_lower:
            rename_map[col] = "grande_area"
            
    df.rename(columns=rename_map, inplace=True)
    
    # Garante que as colunas essenciais existem
    for col in ["titulo_revista", "aims_scope", "indexador", "jif", "sjr", "grande_area", "issn", "homepage", "quartil_jcr", "sjr_quartile", "h_index", "h5_link"]:
        if col not in df.columns:
            df[col] = "-"
            
    return df

import functools

@functools.lru_cache(maxsize=1)
def obter_modelo_embeddings():
    """Retorna o modelo de embeddings pré-carregado em memória (all-MiniLM-L6-v2)."""
    return SentenceTransformer(MODEL_NAME)

@functools.lru_cache(maxsize=1)
def carregar_embeddings_cache_global():
    """Carrega os embeddings do catálogo aims_scope_minilm_vectors.pkl instantaneamente da memória."""
    path = os.path.join(BASE_DIR, "data", "aims_scope_minilm_vectors.pkl")
    if not os.path.exists(path):
        path = EMBEDDINGS_CACHE_PATH
    if os.path.exists(path):
        with open(path, "rb") as f:
            return pickle.load(f)
    raise FileNotFoundError(f"Cache de embeddings não encontrado em {path}")

def precomputar_e_salvar_embeddings(df, model):
    """Calcula os embeddings dos escopos e salva em cache."""
    print("Precomputando embeddings para a base de dados de periódicos...")
    escopos = df["aims_scope"].fillna("").astype(str).tolist()
    embeddings = model.encode(escopos, batch_size=256, show_progress_bar=True, convert_to_numpy=True)
    os.makedirs(os.path.dirname(EMBEDDINGS_CACHE_PATH), exist_ok=True)
    with open(EMBEDDINGS_CACHE_PATH, "wb") as f:
        pickle.dump(embeddings, f)
    print(f"Embeddings salvos com sucesso em: {EMBEDDINGS_CACHE_PATH}")
    return embeddings

def carregar_embeddings_cache(df, model):
    """Tenta carregar os embeddings pré-calculados em fração de segundo."""
    try:
        embeddings = carregar_embeddings_cache_global()
        if len(embeddings) == len(df):
            return embeddings
        elif len(embeddings) > len(df):
            return embeddings[:len(df)]
        else:
            print(f"Aviso: Cache de embeddings ({len(embeddings)}) menor que o DataFrame ({len(df)}). Usando disponível.")
            return embeddings
    except Exception as e:
        print(f"Erro ao carregar cache de embeddings: {e}. Recriando...")
        return precomputar_e_salvar_embeddings(df, model)

# 🌐 DICIONÁRIO DE PONTE TRILÍNGUE AUTOMÁTICA
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

def normalizar_texto(txt):
    if not txt or not isinstance(txt, str):
        return ""
    import unicodedata
    nfkd = unicodedata.normalize('NFKD', txt)
    return "".join([c for c in nfkd if not unicodedata.combining(c)]).lower().strip()

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

def calcular_probabilidade_aceitacao(row):
    """Calcula a Probabilidade Proxy de Aceitação (%) com tratamento robusto para periódicos com e sem Fator de Impacto."""
    s_text = float(row.get("S_text", 0.5))
    jif_val = float(row.get("jif_parsed", 0.0))
    sjr_val = float(row.get("sjr_parsed", 0.0))
    fator_imp = max(jif_val, sjr_val)
    
    q_jcr = str(row.get("quartil_jcr", "")).upper()
    q_sjr = str(row.get("sjr_quartile", "")).upper()

    possui_impacto = (fator_imp > 0.0) or ("Q" in q_jcr) or ("Q" in q_sjr)

    if possui_impacto:
        dificuldade_q = 0.85 if ("Q1" in q_jcr or "Q1" in q_sjr) else (0.65 if ("Q2" in q_jcr or "Q2" in q_sjr) else (0.45 if ("Q3" in q_jcr or "Q3" in q_sjr) else 0.25))
        dificuldade_jif = min(1.0, fator_imp / 10.0)
        dificuldade = 0.40 * dificuldade_jif + 0.35 * dificuldade_q + 0.25 * (1.0 - s_text)
    else:
        # 📌 TRATAMENTO PARA REVISTAS SEM FATOR DE IMPACTO (Utiliza o Nível do Indexador como Proxy de Seletividade)
        s_idx = float(row.get("S_index", 0.3))
        if s_idx >= 1.0:
            dif_base = 0.65
        elif s_idx >= 0.8:
            dif_base = 0.50
        elif s_idx >= 0.7:
            dif_base = 0.45
        elif s_idx >= 0.6:
            dif_base = 0.40
        elif s_idx >= 0.5:
            dif_base = 0.35
        elif s_idx >= 0.4:
            dif_base = 0.30
        else:
            dif_base = 0.20
            
        dificuldade = 0.60 * dif_base + 0.40 * (1.0 - s_text)

    prob = (s_text * 0.65 + (1.0 - dificuldade) * 0.35) * 100.0
    return int(min(85, max(15, round(prob))))

def recomendar_periodicos(titulo, resumo, top_n=100, filtrar_area=True, area_manual=None, indexador_manual=None, area=None, indexador=None, **kwargs):
    """
    Executa o algoritmo HÍBRIDO (Transformer + TF-IDF + Ponte Trilíngue + Métrica Proxy de Aceite sem JIF).
    """
    if not area_manual and area:
        area_manual = area
    if not indexador_manual and indexador:
        indexador_manual = indexador

    # 1. Carrega e normaliza os dados
    df = carregar_e_normalizar_base()
    
    # 2. Identifica a Grande Área do artigo e filtra se solicitado
    area_msg = ""
    if area_manual and str(area_manual).strip() not in ["Todas", "Todas as Áreas", "Todas as Áreas / Broad Areas", "-"]:
        mask = df["grande_area"].apply(lambda x: str(area_manual).lower() in str(x).lower())
        df_filtered = df[mask].copy()
        if len(df_filtered) == 0:
            df_filtered = df.copy()
            indices_validos = list(range(len(df)))
        else:
            indices_validos = df_filtered.index.tolist()
    elif filtrar_area:
        areas_detectadas = identificar_grandes_areas(titulo, resumo)
        area_msg = f"Grande(s) Área(s) detectada(s): {', '.join(areas_detectadas)}"
        print(area_msg)
        
        mask = df["grande_area"].apply(
            lambda x: any(area.lower() in str(x).lower() for area in areas_detectadas)
        )
        df_filtered = df[mask].copy()
        
        if len(df_filtered) == 0:
            print("Nenhum periódico encontrado na Grande Área filtrada. Mantendo catálogo completo.")
            df_filtered = df.copy()
            indices_validos = list(range(len(df)))
        else:
            indices_validos = df_filtered.index.tolist()
    else:
        df_filtered = df.copy()
        indices_validos = list(range(len(df)))
        
    # Filtra por indexador se especificado
    if indexador_manual and str(indexador_manual).strip() not in ["Todos", "ia_todos", "Todos os Indexadores", "-"]:
        mask_idx = df_filtered["indexador"].apply(lambda x: str(indexador_manual).lower() in str(x).lower())
        df_idx = df_filtered[mask_idx].copy()
        if len(df_idx) > 0:
            df_filtered = df_idx
            indices_validos = df_filtered.index.tolist()
        
    # 3. Carrega modelo Transformer e embeddings do catálogo
    model = obter_modelo_embeddings()
    catalog_embeddings_all = carregar_embeddings_cache(df, model)
    catalog_embeddings = catalog_embeddings_all[indices_validos]
    
    # 4. Processa entrada do manuscrito com PONTE TRILÍNGUE e REFORÇO NO TÍTULO (3X)
    texto_trilingue = expandir_texto_trilingue(f"{titulo} {resumo}")
    manuscrito_texto = f"{titulo} {titulo} {titulo} {resumo} {texto_trilingue}".strip()
    manuscrito_embedding = model.encode([manuscrito_texto], convert_to_numpy=True)
    
    # 5. Similaridade Semântica Densa (S_text)
    sim_dense = cosine_similarity(manuscrito_embedding, catalog_embeddings).flatten()
    sim_dense = np.nan_to_num(sim_dense, nan=0.0)
    
    # 6. Similaridade Esparsa TF-IDF (S_sparse)
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        escopos_fl = df_filtered["aims_scope"].fillna("").astype(str).tolist()
        tfidf_vec = TfidfVectorizer(max_features=16000, stop_words='english')
        tfidf_matrix = tfidf_vec.fit_transform(escopos_fl)
        v_sparse = tfidf_vec.transform([manuscrito_texto])
        sim_sparse = cosine_similarity(v_sparse, tfidf_matrix).flatten()
        sim_sparse = np.nan_to_num(sim_sparse, nan=0.0)
    except Exception:
        sim_sparse = np.zeros(len(df_filtered))

    df_filtered["S_text"] = sim_dense
    df_filtered["S_sparse"] = sim_sparse
    
    # Calcula fator_impacto
    df_filtered["jif_parsed"] = df_filtered["jif"].apply(safe_float)
    df_filtered["sjr_parsed"] = df_filtered["sjr"].apply(safe_float)
    df_filtered["fator_impacto"] = df_filtered[["jif_parsed", "sjr_parsed"]].max(axis=1).fillna(0.0)
    
    top_indices = np.argsort(sim_dense)[::-1][:100]
    df_candidates = df_filtered.iloc[top_indices].copy()
    
    df_candidates["S_index"] = df_candidates["indexador"].apply(get_s_index)
    
    # 📌 FÓRMULA HÍBRIDA (65% Dense + 15% Sparse + 20% Indexador)
    df_candidates["Score_final"] = (0.65 * df_candidates["S_text"] + 0.15 * df_candidates["S_sparse"] + 0.20 * df_candidates["S_index"]).fillna(0.0)
    
    # 📌 CÁLCULO DA PROBABILIDADE PROXY DE ACEITAÇÃO (%)
    df_candidates["Prob_aceitacao"] = df_candidates.apply(calcular_probabilidade_aceitacao, axis=1)

    df_ranked = df_candidates.sort_values(
        by=["Score_final", "fator_impacto", "S_text"],
        ascending=[False, False, False]
    )
    
    cols_to_show = [
        "titulo_revista", "issn", "homepage", "aims_scope", "indexador", "jif", "quartil_jcr", "sjr", "sjr_quartile", "h_index", "h5_link", "grande_area",
        "S_text", "S_sparse", "S_index", "fator_impacto", "Score_final", "Prob_aceitacao"
    ]
    
    return df_ranked[cols_to_show].head(top_n)

if __name__ == "__main__":
    print("Testando inicialização do recomendador otimizado HÍBRIDO...")
    df_test = recomendar_periodicos(
        titulo="Humane: estudo piloto para validação de instrumento sobre Humanização na Educação Musical",
        resumo="Este estudo piloto objetivou desenvolver e validar o questionário Humane na Educação Musical.",
        top_n=5,
        filtrar_area=True
    )
    print("\nResultados do teste HÍBRIDO (Top 5):")
    print(df_test[["titulo_revista", "grande_area", "Score_final", "Prob_aceitacao", "fator_impacto", "S_text", "S_index"]])

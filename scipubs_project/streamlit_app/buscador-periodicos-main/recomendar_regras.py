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

def recomendar_periodicos(titulo, resumo, top_n=100, filtrar_area=True, area_manual=None, indexador_manual=None, area=None, indexador=None, **kwargs):
    """
    Executa o algoritmo de recomendação de periódicos científicos com as otimizações.
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
        
        # Filtra o dataframe original para manter apenas revistas das áreas identificadas
        mask = df["grande_area"].apply(
            lambda x: any(area.lower() in str(x).lower() for area in areas_detectadas)
        )
        df_filtered = df[mask].copy()
        
        # Se o filtro resultar em nada, mantém tudo como fallback
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
        
    # 3. Carrega modelo e embeddings do catálogo
    model = obter_modelo_embeddings()
    catalog_embeddings_all = carregar_embeddings_cache(df, model)
    
    # Filtra a matriz de embeddings do catálogo para bater com os índices válidos
    catalog_embeddings = catalog_embeddings_all[indices_validos]
    
    # 4. Processa entrada do manuscrito
    # Repete o título 3 vezes para valorizar o tema em relação à metodologia descrita no resumo
    manuscrito_texto = f"{titulo} {titulo} {titulo} {resumo}".strip()
    manuscrito_embedding = model.encode([manuscrito_texto], convert_to_numpy=True)
    
    # 5. Similaridade Semântica (S_text)
    similarities = cosine_similarity(manuscrito_embedding, catalog_embeddings).flatten()
    
    # Trata NaN que podem ocorrer se embeddings forem corrompidos
    similarities = np.nan_to_num(similarities, nan=0.0)
    
    # Atribui S_text ao DataFrame filtrado
    df_filtered["S_text"] = similarities
    
    # Calcula fator_impacto (trata NaN como 0.0)
    df_filtered["jif_parsed"] = df_filtered["jif"].apply(safe_float)
    df_filtered["sjr_parsed"] = df_filtered["sjr"].apply(safe_float)
    df_filtered["fator_impacto"] = df_filtered[["jif_parsed", "sjr_parsed"]].max(axis=1).fillna(0.0)
    
    # Etapa 1 (Filtro de Candidatos): Seleciona os Top 100 periódicos com maior S_text do conjunto filtrado
    top_indices = np.argsort(similarities)[::-1][:100]
    df_candidates = df_filtered.iloc[top_indices].copy()
    
    # Etapa 2 (Reranking): Calcula S_index e Score_final apenas para os Top 100
    df_candidates["S_index"] = df_candidates["indexador"].apply(get_s_index)
    
    # Fórmula atualizada com novos pesos (80% S_text + 20% S_index)
    df_candidates["Score_final"] = (0.80 * df_candidates["S_text"] + 0.20 * df_candidates["S_index"]).fillna(0.0)
    
    # Ordenação e critério de desempate:
    # 1. Score_final (DECRESCENTE)
    # 2. fator_impacto (DECRESCENTE)
    # 3. S_text (DECRESCENTE)
    df_ranked = df_candidates.sort_values(
        by=["Score_final", "fator_impacto", "S_text"],
        ascending=[False, False, False]
    )
    
    # Seleciona as colunas finais relevantes para exibição
    cols_to_show = [
        "titulo_revista", "issn", "homepage", "aims_scope", "indexador", "jif", "quartil_jcr", "sjr", "sjr_quartile", "h_index", "h5_link", "grande_area",
        "S_text", "S_index", "fator_impacto", "Score_final"
    ]
    
    return df_ranked[cols_to_show].head(top_n)

if __name__ == "__main__":
    # Teste de execução rápida
    print("Testando inicialização do recomendador otimizado...")
    df_test = recomendar_periodicos(
        titulo="Humane: estudo piloto para validação de instrumento sobre Humanização na Educação Musical",
        resumo="Este estudo piloto objetivou desenvolver e validar o questionário Humane na Educação Musical.",
        top_n=5,
        filtrar_area=True
    )
    print("\nResultados do teste (Top 5):")
    print(df_test[["titulo_revista", "grande_area", "Score_final", "fator_impacto", "S_text", "S_index"]])

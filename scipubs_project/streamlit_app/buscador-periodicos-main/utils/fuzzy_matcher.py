"""
Fuzzy Matcher
Utilitários para matching difuso de strings (SequenceMatcher)
"""

from difflib import SequenceMatcher
from typing import Tuple, Optional
import pandas as pd
from .normalizer import normalize_string, clean_journal_name


def calculate_similarity(str1: str, str2: str) -> float:
    """
    Calcula similaridade entre duas strings (0-1)
    
    Usa SequenceMatcher do difflib
    
    Args:
        str1: Primeira string
        str2: Segunda string
        
    Returns:
        Score de similaridade (0 a 1)
    """
    if not str1 or not str2:
        return 0.0
    
    # Normaliza strings
    norm1 = normalize_string(str1)
    norm2 = normalize_string(str2)
    
    # Calcula similaridade
    return SequenceMatcher(None, norm1, norm2).ratio()


def find_journal_in_dataframe(
    journal_name: str,
    df: pd.DataFrame,
    name_column: str = "Título da Revista",
    threshold: float = 0.82,
    use_clean_name: bool = True
) -> Tuple[Optional[pd.Series], float]:
    """
    Busca revista no dataframe usando fuzzy matching
    
    Args:
        journal_name: Nome da revista a buscar
        df: DataFrame com revistas
        name_column: Nome da coluna com nomes das revistas
        threshold: Limiar de similaridade (default: 0.82)
        use_clean_name: Se True, usa clean_journal_name para comparação
        
    Returns:
        Tupla (linha encontrada, score) ou (None, 0) se não encontrado
    """
    if name_column not in df.columns:
        return None, 0.0
    
    best_score = 0.0
    best_row = None
    best_index = None
    
    # Normaliza nome de busca
    search_name = clean_journal_name(journal_name) if use_clean_name else normalize_string(journal_name)
    
    for idx, row in df.iterrows():
        df_name = str(row[name_column])
        df_name_clean = clean_journal_name(df_name) if use_clean_name else normalize_string(df_name)
        
        score = SequenceMatcher(None, search_name, df_name_clean).ratio()
        
        if score > best_score:
            best_score = score
            best_row = row
            best_index = idx
    
    if best_score >= threshold:
        return best_row, best_score
    
    return None, 0.0


def find_journal_by_issn(
    issn: str,
    df: pd.DataFrame,
    issn_column: str = "ISSN"
) -> Optional[pd.Series]:
    """
    Busca revista por ISSN no dataframe
    
    Args:
        issn: ISSN a buscar
        df: DataFrame com revistas
        issn_column: Nome da coluna com ISSN
        
    Returns:
        Linha encontrada ou None
    """
    from .normalizer import normalize_issn
    
    if issn_column not in df.columns:
        return None
    
    issn_clean = normalize_issn(issn)
    if not issn_clean:
        return None
    
    # Tenta match exato
    match = df[df[issn_column].astype(str).str.replace("-", "").str.strip() == issn_clean]
    
    if not match.empty:
        return match.iloc[0]
    
    return None


def batch_match_journals(
    journal_names: list,
    df: pd.DataFrame,
    name_column: str = "Título da Revista",
    threshold: float = 0.82
) -> dict:
    """
    Faz matching em lote de revistas
    
    Args:
        journal_names: Lista de nomes de revistas
        df: DataFrame com revistas
        name_column: Nome da coluna com nomes
        threshold: Limiar de similaridade
        
    Returns:
        Dicionário {nome_revista: (linha_encontrada, score)}
    """
    results = {}
    
    for name in journal_names:
        row, score = find_journal_in_dataframe(name, df, name_column, threshold)
        results[name] = (row, score)
    
    return results


def find_best_match(
    query: str,
    candidates: list,
    threshold: float = 0.82
) -> Tuple[Optional[str], float]:
    """
    Encontra melhor match entre query e lista de candidatos
    
    Args:
        query: String de busca
        candidates: Lista de strings candidatas
        threshold: Limiar de similaridade
        
    Returns:
        Tupla (melhor_candidato, score) ou (None, 0)
    """
    best_score = 0.0
    best_match = None
    
    query_norm = normalize_string(query)
    
    for candidate in candidates:
        candidate_norm = normalize_string(candidate)
        score = SequenceMatcher(None, query_norm, candidate_norm).ratio()
        
        if score > best_score:
            best_score = score
            best_match = candidate
    
    if best_score >= threshold:
        return best_match, best_score
    
    return None, 0.0

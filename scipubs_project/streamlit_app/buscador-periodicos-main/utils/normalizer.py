"""
String Normalizer
Utilitários para normalização e comparação de strings
"""

import unicodedata
import re
from typing import Optional


def normalize_string(text: str) -> str:
    """
    Normaliza string para comparação
    
    Remove acentos, converte para minúsculas, remove caracteres especiais
    
    Args:
        text: String a normalizar
        
    Returns:
        String normalizada
    """
    if not text:
        return ""
    
    # Converte para minúsculas
    text = str(text).lower().strip()
    
    # Remove acentos
    text = ''.join(c for c in unicodedata.normalize('NFD', text) 
                   if unicodedata.category(c) != 'Mn')
    
    # Remove caracteres especiais (mantém apenas alfanuméricos e espaços)
    text = re.sub(r'[^a-z0-9\s]', '', text)
    
    # Remove espaços extras
    text = ' '.join(text.split())
    
    return text


def normalize_issn(issn: Optional[str]) -> Optional[str]:
    """
    Normaliza ISSN (remove hífen e espaços)
    
    Args:
        issn: ISSN a normalizar
        
    Returns:
        ISSN normalizado ou None
    """
    if not issn:
        return None
    
    # Remove hífen e espaços
    issn_clean = str(issn).replace("-", "").replace(" ", "").strip()
    
    # Valida formato (8 dígitos)
    if len(issn_clean) == 8 and issn_clean.isdigit():
        return issn_clean
    
    return None


def extract_issn_from_string(text: str) -> Optional[str]:
    """
    Extrai ISSN de uma string (busca padrão XXXX-XXXX)
    
    Args:
        text: String contendo ISSN
        
    Returns:
        ISSN extraído ou None
    """
    if not text:
        return None
    
    # Padrão ISSN: 4 dígitos, hífen, 4 dígitos
    pattern = r'\b(\d{4}-\d{3}[\dXx])\b'
    match = re.search(pattern, str(text))
    
    if match:
        return normalize_issn(match.group(1))
    
    return None


def clean_journal_name(name: str) -> str:
    """
    Limpa nome de revista para comparação
    
    Remove artigos, preposições comuns e pontuação
    
    Args:
        name: Nome da revista
        
    Returns:
        Nome limpo
    """
    if not name:
        return ""
    
    # Normaliza
    name = normalize_string(name)
    
    # Remove artigos e preposições comuns em português/inglês/espanhol
    stop_words = {
        'the', 'a', 'an', 'of', 'and', 'or', 'for', 'in', 'on', 'at', 'by',
        'o', 'a', 'os', 'as', 'um', 'uma', 'de', 'do', 'da', 'dos', 'das',
        'e', 'em', 'para', 'por', 'com', 'sem', 'sobre',
        'el', 'la', 'los', 'las', 'un', 'una', 'de', 'del', 'y', 'en', 'para', 'por', 'con'
    }
    
    words = name.split()
    words = [w for w in words if w not in stop_words and len(w) > 1]
    
    return ' '.join(words)


def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Trunca string se exceder tamanho máximo
    
    Args:
        text: String a truncar
        max_length: Tamanho máximo
        suffix: Sufixo a adicionar se truncado
        
    Returns:
        String truncada ou original
    """
    if not text:
        return ""
    
    text = str(text)
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

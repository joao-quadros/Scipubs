"""
Validadores para scores e resultados de recomendações
"""

from typing import Tuple, Optional, List, Dict


def validate_score(valor, campo_nome: str, min_val: int = 0, max_val: int = 100) -> Tuple[int, Optional[str]]:
    """
    Valida que um score está entre 0-100
    
    Args:
        valor: Valor a ser validado
        campo_nome: Nome do campo para mensagem de erro
        min_val: Valor mínimo (default: 0)
        max_val: Valor máximo (default: 100)
        
    Returns:
        (valor_validado, erro_ou_none)
    """
    try:
        if isinstance(valor, str):
            valor = int(valor.replace("%", "").strip())
        else:
            valor = int(valor)
        
        if valor < min_val or valor > max_val:
            return max(min_val, min(max_val, valor)), (
                f"⚠️ {campo_nome} {valor}% normalizado para "
                f"{max(min_val, min(max_val, valor))}%"
            )
        
        return valor, None
    
    except (ValueError, TypeError):
        return 50, f"❌ {campo_nome} inválido: {valor}. Usando padrão 50%."


def validate_recommendation_result(recommendation: dict) -> Tuple[dict, Optional[str]]:
    """
    Valida estrutura completa de recomendação
    
    Args:
        recommendation: Dicionário com dados da recomendação
        
    Returns:
        (recomendacao_validada, erro_ou_none)
    """
    campos_obrigatorios = ["nome", "aderencia", "justificativa"]
    
    erros = []
    
    for campo in campos_obrigatorios:
        if campo not in recommendation:
            erros.append(f"Campo faltando: {campo}")
    
    if not recommendation.get("nome", "").strip():
        erros.append("Nome da revista vazio")
    
    score, erro = validate_score(
        recommendation.get("aderencia", 50),
        "aderencia"
    )
    recommendation["aderencia"] = score
    if erro:
        erros.append(erro)
    
    justificativa = str(recommendation.get("justificativa", "")).strip()
    if not justificativa or len(justificativa) < 5:
        recommendation["justificativa"] = "Recomendado com base na análise temática."
    
    if erros:
        return recommendation, " | ".join(erros)
    
    return recommendation, None


def validate_batch_recommendations(recommendations: list) -> Tuple[list, list]:
    """
    Valida lista de recomendações
    
    Args:
        recommendations: Lista de dicionários de recomendação
        
    Returns:
        (recomendacoes_validas, lista_de_erros)
    """
    validas = []
    erros_lista = []
    
    for idx, rec in enumerate(recommendations):
        rec_valida, erro = validate_recommendation_result(rec)
        validas.append(rec_valida)
        
        if erro:
            erros_lista.append({
                "index": idx,
                "revista": rec.get("nome", "DESCONHECIDA"),
                "erro": erro
            })
    
    return validas, erros_lista
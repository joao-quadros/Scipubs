"""
Módulo de serviços - Inicialização e factories
Sem dependência direta de Streamlit para evitar erros de import
"""
import sys
import importlib
import os


def validate_dependencies(suppress_errors=False):
    """Valida dependências obrigatórias. Retorna lista de módulos faltando."""
    missing = []
    for name, package in [("requests", "requests"), ("pandas", "pandas")]:
        try:
            importlib.import_module(name)
        except ImportError:
            missing.append(package)
    return missing


def check_ollama_available():
    """Verifica se Ollama está disponível localmente"""
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=3)
        if response.status_code == 200:
            models = response.json().get("models", [])
            has_llama3 = any("llama3" in m.get("name", "") for m in models)
            return True, "Pronto" if has_llama3 else "Sem Llama 3"
        return False, f"HTTP {response.status_code}"
    except ImportError:
        return False, "ollama não instalado"
    except Exception as e:
        return False, str(e)


def get_discovery_recommender(df_local, api_key_gemini=None):
    """Factory para DiscoveryRecommender"""
    from services.discovery_recommender import DiscoveryRecommender
    return DiscoveryRecommender(df_local=df_local, api_key_gemini=api_key_gemini)


def get_similar_articles_finder(email_openalex=None):
    """Factory para SimilarArticlesFinder"""
    from services.similar_articles_finder import SimilarArticlesFinder
    return SimilarArticlesFinder(email_openalex=email_openalex)


def get_article_evaluator(df_local, ollama_model="llama3"):
    """Factory para ArticleEvaluator"""
    from services.article_evaluator import ArticleEvaluator
    return ArticleEvaluator(df_local=df_local, ollama_model=ollama_model)


def get_cache_manager():
    """Factory para CacheManager"""
    from services.cache_manager import CacheManager
    return CacheManager()
"""
Anonymous Logger
Sistema de logging anônimo para monitoramento sem dados pessoais
"""

import json
import os
from datetime import datetime
from typing import Dict, Optional
import threading


class AnonymousLogger:
    """Logger anônimo para métricas de uso"""
    
    def __init__(self, log_dir: str = "logs"):
        """
        Inicializa logger anônimo
        
        Args:
            log_dir: Diretório para armazenar logs
        """
        self.log_dir = log_dir
        self._lock = threading.Lock()
        
        # Cria diretório se não existe
        os.makedirs(log_dir, exist_ok=True)
    
    def log_recommendation(
        self,
        area_conhecimento: str,
        tempo_resposta_segundos: float,
        num_resultados: int,
        sucesso: bool = True,
        idioma: str = "Português"
    ):
        """
        Log de requisição de recomendação (anônimo)
        
        Args:
            area_conhecimento: Área do conhecimento (não armazena título)
            tempo_resposta_segundos: Tempo de resposta
            num_resultados: Número de resultados
            sucesso: Se a operação foi bem-sucedida
            idioma: Idioma da interface
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "tipo": "recomendacao",
            "area_conhecimento": area_conhecimento,
            "tempo_resposta_segundos": round(tempo_resposta_segundos, 2),
            "num_resultados": num_resultados,
            "sucesso": sucesso,
            "idioma": idioma
        }
        
        self._write_log(log_entry)
    
    def log_search(
        self,
        area_conhecimento: str,
        num_resultados: int,
        filtros_usados: Dict,
        idioma: str = "Português"
    ):
        """
        Log de busca tradicional (anônimo)
        
        Args:
            area_conhecimento: Área do conhecimento
            num_resultados: Número de resultados
            filtros_usados: Filtros aplicados
            idioma: Idioma da interface
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "tipo": "busca_tradicional",
            "area_conhecimento": area_conhecimento,
            "num_resultados": num_resultados,
            "filtros_usados": filtros_usados,
            "idioma": idioma
        }
        
        self._write_log(log_entry)
    
    def log_similar_articles(
        self,
        tempo_resposta_segundos: float,
        num_artigos: int,
        sucesso: bool = True
    ):
        """
        Log de busca de artigos similares (anônimo)
        
        Args:
            tempo_resposta_segundos: Tempo de resposta
            num_artigos: Número de artigos encontrados
            sucesso: Se a operação foi bem-sucedida
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "tipo": "artigos_similares",
            "tempo_resposta_segundos": round(tempo_resposta_segundos, 2),
            "num_artigos": num_artigos,
            "sucesso": sucesso
        }
        
        self._write_log(log_entry)
    
    def log_error(
        self,
        tipo_erro: str,
        componente: str,
        mensagem: str
    ):
        """
        Log de erro (anônimo)
        
        Args:
            tipo_erro: Tipo do erro
            componente: Componente onde ocorreu
            mensagem: Mensagem de erro
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "tipo": "erro",
            "tipo_erro": tipo_erro,
            "componente": componente,
            "mensagem": mensagem
        }
        
        self._write_log(log_entry)
    
    def log_feedback(
        self,
        rating: int,
        comentario: Optional[str] = None
    ):
        """
        Log de feedback opcional (anônimo)
        
        Args:
            rating: Avaliação (1-5)
            comentario: Comentário opcional
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "tipo": "feedback",
            "rating": rating,
            "comentario": comentario if comentario else ""
        }
        
        self._write_log(log_entry)
    
    def _write_log(self, log_entry: Dict):
        """
        Escreve entrada no arquivo de log
        
        Args:
            log_entry: Dicionário com dados do log
        """
        with self._lock:
            # Nome do arquivo baseado na data
            date_str = datetime.now().strftime("%Y-%m-%d")
            log_file = os.path.join(self.log_dir, f"scipubs_{date_str}.jsonl")
            
            # Escreve em formato JSONL (uma linha por entrada)
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    
    def get_daily_stats(self, date: Optional[str] = None) -> Dict:
        """
        Retorna estatísticas de um dia específico
        
        Args:
            date: Data no formato YYYY-MM-DD (default: hoje)
            
        Returns:
            Dicionário com estatísticas
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        log_file = os.path.join(self.log_dir, f"scipubs_{date}.jsonl")
        
        if not os.path.exists(log_file):
            return {}
        
        stats = {
            "total_recomendacoes": 0,
            "total_buscas": 0,
            "total_artigos_similares": 0,
            "total_erros": 0,
            "total_feedbacks": 0,
            "areas_mais_pesquisadas": {},
            "tempo_medio_recomendacao": 0,
            "taxa_sucesso_recomendacao": 1.0,
            "rating_medio": 0
        }
        
        recomendacao_times = []
        recomendacao_success = 0
        recomendacao_total = 0
        feedback_ratings = []
        
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                for line in f:
                    entry = json.loads(line)
                    
                    if entry["tipo"] == "recomendacao":
                        stats["total_recomendacoes"] += 1
                        recomendacao_times.append(entry["tempo_resposta_segundos"])
                        recomendacao_total += 1
                        if entry["sucesso"]:
                            recomendacao_success += 1
                        
                        area = entry.get("area_conhecimento", "-")
                        stats["areas_mais_pesquisadas"][area] = \
                            stats["areas_mais_pesquisadas"].get(area, 0) + 1
                    
                    elif entry["tipo"] == "busca_tradicional":
                        stats["total_buscas"] += 1
                        
                        area = entry.get("area_conhecimento", "-")
                        stats["areas_mais_pesquisadas"][area] = \
                            stats["areas_mais_pesquisadas"].get(area, 0) + 1
                    
                    elif entry["tipo"] == "artigos_similares":
                        stats["total_artigos_similares"] += 1
                    
                    elif entry["tipo"] == "erro":
                        stats["total_erros"] += 1
                    
                    elif entry["tipo"] == "feedback":
                        stats["total_feedbacks"] += 1
                        feedback_ratings.append(entry["rating"])
            
            # Calcula médias
            if recomendacao_times:
                stats["tempo_medio_recomendacao"] = \
                    sum(recomendacao_times) / len(recomendacao_times)
            
            if recomendacao_total > 0:
                stats["taxa_sucesso_recomendacao"] = \
                    recomendacao_success / recomendacao_total
            
            if feedback_ratings:
                stats["rating_medio"] = sum(feedback_ratings) / len(feedback_ratings)
            
            # Ordena áreas mais pesquisadas
            stats["areas_mais_pesquisadas"] = dict(
                sorted(stats["areas_mais_pesquisadas"].items(), 
                      key=lambda x: x[1], reverse=True)[:10]
            )
            
        except Exception as e:
            print(f"Erro ao ler logs: {e}")
        
        return stats


# Singleton instance
_anonymous_logger = None

def get_anonymous_logger(log_dir: str = "logs") -> AnonymousLogger:
    """
    Retorna instância singleton do AnonymousLogger
    
    Args:
        log_dir: Diretório para logs
        
    Returns:
        Instância de AnonymousLogger
    """
    global _anonymous_logger
    if _anonymous_logger is None:
        _anonymous_logger = AnonymousLogger(log_dir)
    return _anonymous_logger

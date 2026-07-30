"""
Cache Manager
Gerenciador de cache local para reduzir chamadas de API
"""

import sqlite3
import json
import time
import os
from typing import Any, Optional, Dict
from datetime import datetime, timedelta
import hashlib
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CacheManager:
    """Gerenciador de cache usando SQLite"""
    
    def __init__(self, db_path: str = "data/cache.db"):
        """
        Inicializa o gerenciador de cache
        
        Args:
            db_path: Caminho para o banco de dados SQLite
        """
        self.db_path = db_path
        # Garante que o diretório do banco exista
        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Inicializa o banco de dados e cria tabelas"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabela de cache geral
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                value TEXT,
                created_at TIMESTAMP,
                ttl_seconds INTEGER
            )
        """)
        
        # Tabela específica para revistas OpenAlex
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS openalex_journals (
                issn TEXT PRIMARY KEY,
                nome TEXT,
                data TEXT,
                created_at TIMESTAMP,
                ttl_seconds INTEGER DEFAULT 2592000  -- 30 dias
            )
        """)
        
        # Tabela específica para revistas SciELO
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scielo_journals (
                issn TEXT PRIMARY KEY,
                nome TEXT,
                data TEXT,
                created_at TIMESTAMP,
                ttl_seconds INTEGER DEFAULT 2592000  -- 30 dias
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _generate_key(self, prefix: str, *args) -> str:
        """
        Gera chave única para cache
        
        Args:
            prefix: Prefixo da chave
            *args: Argumentos para compor a chave
            
        Returns:
            Chave hash
        """
        key_string = f"{prefix}:{':'.join(str(arg) for arg in args)}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """
        Recupera valor do cache
        
        Args:
            key: Chave do cache
            
        Returns:
            Valor armazenado ou None se expirado/não encontrado
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT value, created_at, ttl_seconds 
            FROM cache 
            WHERE key = ?
        """, (key,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            value, created_at, ttl_seconds = row
            created_dt = datetime.fromisoformat(created_at)
            
            # Verifica se expirou
            if datetime.now() - created_dt < timedelta(seconds=ttl_seconds):
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            else:
                # Remove entrada expirada
                self.delete(key)
        
        return None
    
    def set(self, key: str, value: Any, ttl: int = 3600):
        """
        Armazena valor no cache
        
        Args:
            key: Chave do cache
            value: Valor a armazenar
            ttl: Tempo de vida em segundos (default: 1 hora)
        """
        ttl_seconds = ttl
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Serializa valor se for dict/list
        if isinstance(value, (dict, list)):
            value_str = json.dumps(value)
        else:
            value_str = str(value)
        
        cursor.execute("""
            INSERT OR REPLACE INTO cache (key, value, created_at, ttl_seconds)
            VALUES (?, ?, ?, ?)
        """, (key, value_str, datetime.now().isoformat(), ttl_seconds))
        
        conn.commit()
        conn.close()
    
    def delete(self, key: str):
        """
        Remove entrada do cache
        
        Args:
            key: Chave do cache
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM cache WHERE key = ?", (key,))
        conn.commit()
        conn.close()
    
    def clear_expired(self):
        """Remove todas as entradas expiradas do cache"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM cache 
            WHERE datetime(created_at, '+' || ttl_seconds || ' seconds') < datetime('now')
        """)
        
        cursor.execute("""
            DELETE FROM openalex_journals 
            WHERE datetime(created_at, '+' || ttl_seconds || ' seconds') < datetime('now')
        """)
        
        cursor.execute("""
            DELETE FROM scielo_journals 
            WHERE datetime(created_at, '+' || ttl_seconds || ' seconds') < datetime('now')
        """)
        
        conn.commit()
        conn.close()
        logger.info("Expired cache entries cleared")
    
    def get_openalex_journal(self, issn: str) -> Optional[Dict]:
        """
        Recupera revista OpenAlex do cache
        
        Args:
            issn: ISSN da revista
            
        Returns:
            Dados da revista ou None
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT data, created_at, ttl_seconds 
            FROM openalex_journals 
            WHERE issn = ?
        """, (issn,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            data, created_at, ttl_seconds = row
            created_dt = datetime.fromisoformat(created_at)
            
            if datetime.now() - created_dt < timedelta(seconds=ttl_seconds):
                return json.loads(data)
            else:
                self.delete_openalex_journal(issn)
        
        return None
    
    def set_openalex_journal(self, issn: str, journal_data: Dict, ttl_seconds: int = 2592000):
        """
        Armazena revista OpenAlex no cache
        
        Args:
            issn: ISSN da revista
            journal_data: Dados da revista
            ttl_seconds: Tempo de vida (default: 30 dias)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO openalex_journals (issn, nome, data, created_at, ttl_seconds)
            VALUES (?, ?, ?, ?, ?)
        """, (issn, journal_data.get("nome", ""), json.dumps(journal_data), 
              datetime.now().isoformat(), ttl_seconds))
        
        conn.commit()
        conn.close()
    
    def delete_openalex_journal(self, issn: str):
        """Remove revista OpenAlex do cache"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM openalex_journals WHERE issn = ?", (issn,))
        conn.commit()
        conn.close()
    
    def get_scielo_journal(self, issn: str) -> Optional[Dict]:
        """
        Recupera revista SciELO do cache
        
        Args:
            issn: ISSN da revista
            
        Returns:
            Dados da revista ou None
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT data, created_at, ttl_seconds 
            FROM scielo_journals 
            WHERE issn = ?
        """, (issn,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            data, created_at, ttl_seconds = row
            created_dt = datetime.fromisoformat(created_at)
            
            if datetime.now() - created_dt < timedelta(seconds=ttl_seconds):
                return json.loads(data)
            else:
                self.delete_scielo_journal(issn)
        
        return None
    
    def set_scielo_journal(self, issn: str, journal_data: Dict, ttl_seconds: int = 2592000):
        """
        Armazena revista SciELO no cache
        
        Args:
            issn: ISSN da revista
            journal_data: Dados da revista
            ttl_seconds: Tempo de vida (default: 30 dias)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO scielo_journals (issn, nome, data, created_at, ttl_seconds)
            VALUES (?, ?, ?, ?, ?)
        """, (issn, journal_data.get("nome", ""), json.dumps(journal_data), 
              datetime.now().isoformat(), ttl_seconds))
        
        conn.commit()
        conn.close()
    
    def delete_scielo_journal(self, issn: str):
        """Remove revista SciELO do cache"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM scielo_journals WHERE issn = ?", (issn,))
        conn.commit()
        conn.close()
    
    def get_stats(self) -> Dict:
        """
        Retorna estatísticas do cache
        
        Returns:
            Dicionário com estatísticas
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        # Contagem geral
        cursor.execute("SELECT COUNT(*) FROM cache")
        stats["cache_entries"] = cursor.fetchone()[0]
        
        # Contagem OpenAlex
        cursor.execute("SELECT COUNT(*) FROM openalex_journals")
        stats["openalex_journals"] = cursor.fetchone()[0]
        
        # Contagem SciELO
        cursor.execute("SELECT COUNT(*) FROM scielo_journals")
        stats["scielo_journals"] = cursor.fetchone()[0]
        
        conn.close()
        return stats


# Singleton instance
_cache_manager = None

def get_cache_manager(db_path: str = "data/cache.db") -> CacheManager:
    """
    Retorna instância singleton do CacheManager
    
    Args:
        db_path: Caminho para o banco de dados
        
    Returns:
        Instância de CacheManager
    """
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager(db_path)
    return _cache_manager

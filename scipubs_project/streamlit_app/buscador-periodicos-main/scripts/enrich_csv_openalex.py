#!/usr/bin/env python3
"""
Script para enriquecer dados.csv com informações da OpenAlex API
Adiciona: aims & scope, homepage, dados de citação aprimorados
"""

import pandas as pd
import requests
import time
import json
from typing import Optional, Dict

OPENALEX_BASE = "https://api.openalex.org"

def get_journal_by_issn(issn: str) -> Optional[Dict]:
    """Busca revista na OpenAlex pelo ISSN"""
    if not issn or pd.isna(issn):
        return None
    try:
        # Remove hífens do ISSN
        issn_clean = str(issn).replace("-", "")
        url = f"{OPENALEX_BASE}/journals"
        params = {"filter": f"issn:{issn_clean}"}
        response = requests.get(url, params=params, timeout=10)
        if response.ok:
            data = response.json()
            if data.get("results"):
                return data["results"][0]
    except Exception as e:
        print(f"Erro ao buscar ISSN {issn}: {e}")
    return None

def get_journal_by_name(nome: str) -> Optional[Dict]:
    """Busca revista na OpenAlex pelo nome"""
    if not nome or pd.isna(nome):
        return None
    try:
        url = f"{OPENALEX_BASE}/journals"
        params = {"search": nome, "per_page": 1}
        response = requests.get(url, params=params, timeout=10)
        if response.ok:
            data = response.json()
            if data.get("results"):
                return data["results"][0]
    except Exception as e:
        print(f"Erro ao buscar nome {nome}: {e}")
    return None

def enrich_csv(input_file: str, output_file: str):
    """Enriquece CSV com dados da OpenAlex"""
    df = pd.read_csv(input_file, sep=';', encoding='utf-8')
    
    # Adiciona colunas novas
    if 'aims_scope' not in df.columns:
        df['aims_scope'] = ""
    if 'homepage_openalex' not in df.columns:
        df['homepage_openalex'] = ""
    if 'cited_by_count' not in df.columns:
        df['cited_by_count'] = ""
    
    total = len(df)
    for idx, row in df.iterrows():
        issn = str(row.get('ISSN', '')).strip()
        nome = str(row.get('Título da Revista', row.get('title', ''))).strip()
        
        if not issn:
            continue
            
        journal = get_journal_by_issn(issn)
        if not journal:
            journal = get_journal_by_name(nome)
        
        if journal:
            df.at[idx, 'aims_scope'] = journal.get('description', '')[:500]
            df.at[idx, 'homepage_openalex'] = journal.get('homepage', '')
            df.at[idx, 'cited_by_count'] = str(journal.get('cited_by_count', ''))
            
        if idx % 50 == 0:
            print(f"Progress: {idx}/{total} ({100*idx/total:.1f}%)")
        time.sleep(0.1)  # Rate limit
    
    df.to_csv(output_file, sep=';', index=False, encoding='utf-8')
    print(f"Salvo em {output_file}")

if __name__ == "__main__":
    enrich_csv("dados.csv", "dados_enriquecido.csv")
#!/usr/bin/env python3
"""
Script para mapear o perfil editorial de periódicos.
Extrai: Objetivo e Escopo, Missão, Tipos de Trabalhos Aceitos.
Fontes: Homepage das revistas + CrossRef API.
"""

import os
import time
import pandas as pd
import requests
from bs4 import BeautifulSoup
from typing import Optional, List
import re

# Arquivo original (será atualizado)
CSV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dados_new.csv")


def fetch_crossref(issn: str) -> Optional[str]:
    """Busca informações da revista na CrossRef API"""
    if not issn or len(issn.replace("-", "")) != 8:
        return None
    
    issn_clean = issn.replace("-", "")
    url = f"https://api.crossref.org/journals/{issn_clean}"
    
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            message = data.get("message", {})
            
            parts = []
            # Publisher
            publisher = message.get("publisher", "")
            if publisher:
                parts.append(f"Editora: {publisher}")
            
            # Assuntos
            subjects = message.get("subjects", [])
            if subjects:
                subj_names = [s.get("name", "") for s in subjects if s.get("name")]
                if subj_names:
                    # Limita para não ficar muito longo
                    parts.append(f"Áreas temáticas: {', '.join(subj_names[:10])}")
                    
            # Aviso (description)
            description = message.get("description", "")
            if description and len(str(description).strip()) > 20:
                desc = str(description).strip()
                if len(desc) > 1000:
                    desc = desc[:1000] + "... [truncated]"
                parts.append(f"Visão geral: {desc}")
            
            result = " | ".join(parts) if len(parts) > 1 else None
            return result
    except Exception:
        pass
    return None


def fetch_from_homepage(url: str) -> Optional[str]:
    """Busca Aims & Scope no site da revista."""
    if not url or url in ["-", "", "nan", "None"] or not str(url).strip().startswith("http"):
        return None
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code != 200:
            return None
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Procura links com palavras-chave
        links_to_check = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            text = a.get_text(strip=True).lower()
            if any(kw in text or kw in href.lower() for kw in ['aim', 'scope', 'about', 'mission', 'focus', 'overview', 'journal']):
                if href.startswith('http'):
                    links_to_check.append(href)
                elif href.startswith('/'):
                    base = '/'.join(url.split('/')[:3])
                    links_to_check.append(base + href)
        
        # Também procura conteúdo no próprio page
        content = []
        main_div = soup.find('main') or soup.find('article') or soup.find('div', class_=re.compile(r'content|main|article'))
        
        if main_div:
            for p in main_div.find_all(['p', 'div', 'span', 'li']):
                text = p.get_text(strip=True)
                if 100 < len(text) < 2000:
                    content.append(text)
        
        # Limita conteúdo
        if content:
            text = ' '.join(content[:10])
            if len(text) > 1500:
                text = text[:1500] + "..."
            return text
        
        return None
    except Exception as e:
        return None


def fetch_specific_pages(base_url: str, title: str) -> Optional[str]:
    """Tenta buscar páginas específicas de Aims & Scope"""
    keywords = ['about', 'aims', 'scope', 'mission', 'focus', 'overview']
    
    # Tenta diferentes padrões de URL
    patterns = [
        f"{base_url.rstrip('/')}/about",
        f"{base_url.rstrip('/')}/aims",
        f"{base_url.rstrip('/')}/scope",
        f"{base_url.rstrip('/')}/about-the-journal",
        f"{base_url.rstrip('/')}/journalAimsAndScope",
        f"{base_url.rstrip('/')}/pages/view/aims-scope",
        f"{base_url.rstrip('/')}/aims-and-scope",
        f"{base_url.rstrip('/')}/editorial-info",
    ]
    
    headers = {"User-Agent": "Mozilla/5.0"}
    
    for url in patterns:
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                text_elements = []
                for p in soup.find_all(['p', 'div', 'span']):
                    text = p.get_text(strip=True)
                    if 100 <= len(text) <= 2000:
                        text_elements.append(text)
                
                if text_elements:
                    result = ' '.join(text_elements[:15])
                    if len(result) > 1500:
                        result = result[:1500] + "..."
                    return result
        except:
            continue
    return None


def main():
    print("=" * 60)
    print("Mapeamento de Perfil Editorial de Periódicos")
    print("=" * 60)
    
    # Lê CSV
    print(f"\nLendo {CSV_PATH}...")
    df = pd.read_csv(CSV_PATH, sep=";", encoding="latin-1", on_bad_lines="skip")
    print(f"Total registros: {len(df)}")
    
    # Identifica colunas
    title_col = "Título da Revista"
    issn_col = "ISSN"
    homepage_col = "Homepage"
    aims_col = "Aims and Scope (translate)"
    
    # Garante coluna Perfil_Editorial
    if "Perfil_Editorial" not in df.columns:
        df["Perfil_Editorial"] = ""
    
    # Encontra registros vazios
    mask_vazio = df["Perfil_Editorial"].isna() | (df["Perfil_Editorial"].astype(str).str.strip().str.len() <= 10)
    indices = df[mask_vazio].index.tolist()
    total_buscar = len(indices)
    print(f"Periódicos para buscar informações: {total_buscar}")
    
    if total_buscar == 0:
        print("Nada a atualizar!")
        return
    
    # Processa em lotes para não sobrecarregar
    batch_size = 20
    success = 0
    not_found = 0
    
    print(f"\nProcessando {min(batch_size, total_buscar)} periódicos...")
    
    for i, idx in enumerate(indices[:batch_size]):
        issn = str(df.at[idx, issn_col]).strip()
        homepage = str(df.at[idx, homepage_col]).strip()
        title = str(df.at[idx, title_col]).strip()
        
        perfil = None
        
        # Tenta CrossRef primeiro
        if issn:
            perfil = fetch_crossref(issn)
        
        # Se não encontrar, tenta homepage
        if not perfil and homepage:
            perfil = fetch_specific_pages(homepage, title)
            if not perfil:
                perfil = fetch_from_homepage(homepage)
        
        if perfil:
            df.at[idx, "Perfil_Editorial"] = perfil[:1500]
            success += 1
            print(f"  [{i+1}] ✓ {title[:50]}")
        else:
            df.at[idx, "Perfil_Editorial"] = "Informação não encontrada"
            not_found += 1
            print(f"  [{i+1}] ✗ {title[:50]}")
        
        time.sleep(0.3)
    
    # Salva no arquivo original
    df.to_csv(CSV_PATH, index=False, encoding="utf-8-sig", sep=";")
    
    print("\n" + "=" * 60)
    print(f"ATUALIZADO: Sucesso={success}, Não encontrado={not_found}")
    print(f"Arquivo atualizado: {CSV_PATH}")
    print("=" * 60)
    
    # Mostra exemplos
    print("\nExemplos de perfis encontrados:")
    samples = df[df["Perfil_Editorial"].notna() & (df["Perfil_Editorial"].str.len() > 50)].head(3)
    for idx, row in samples.iterrows():
        print(f"\n{row[title_col]}:")
        print(f"  {str(row['Perfil_Editorial'])[:300]}...")


if __name__ == "__main__":
    main()
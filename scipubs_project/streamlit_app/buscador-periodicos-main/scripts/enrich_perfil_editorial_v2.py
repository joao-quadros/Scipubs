#!/usr/bin/env python3
"""
Enriquece o Perfil Editorial dos periódicos usando múltiplas fontes.
"""

import os
import time
import pandas as pd
import requests
from bs4 import BeautifulSoup
import warnings
warnings.filterwarnings('ignore')

CSV_PATH = "C:/Users/jquad/Documents/app-revista/dados_new.csv"
BACKUP_PATH = "C:/Users/jquad/Documents/app-revista/dados_new_backup.csv"


def fetch_crossref(issn: str) -> str:
    """Busca informações na CrossRef API"""
    if not issn or len(issn.replace("-", "")) != 8:
        return ""
    
    issn_clean = issn.replace("-", "")
    url = f"https://api.crossref.org/journals/{issn_clean}"
    
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            message = data.get("message", {})
            
            parts = []
            publisher = message.get("publisher", "")
            if publisher:
                parts.append(f"Editora: {publisher}")
            
            subjects = message.get("subjects", [])
            if subjects:
                subj_names = [str(s.get("name", "")) for s in subjects if s.get("name")]
                if subj_names:
                    parts.append(f"Áreas: {', '.join(subj_names[:8])}")
            
            description = message.get("description", "")
            if description and len(str(description).strip()) > 30:
                desc = str(description).strip()[:800]
                parts.append(f"Visão geral: {desc}")
            
            return " | ".join(parts) if parts else ""
    except:
        pass
    return ""


def fetch_from_homepage(url: str, title: str) -> str:
    """Busca no site da revista"""
    if not url or url in ["-", ""] or not str(url).strip().startswith("http"):
        return ""
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    paths = ["/about", "/aims", "/scope", "/about-the-journal", "/aims-and-scope", 
             "/focus-and-scope", "/introduction", "/editorial-board"]
    
    urls_to_try = [url.rstrip('/')]
    for p in paths:
        urls_to_try.append(url.rstrip('/') + p)
    
    for test_url in urls_to_try[:5]:
        try:
            resp = requests.get(test_url, headers=headers, timeout=10)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                
                texts = []
                for p in soup.find_all(['p', 'div', 'span', 'li']):
                    txt = p.get_text(strip=True)
                    if 100 <= len(txt) <= 2000:
                        if any(kw in txt.lower() for kw in ['scope', 'aim', 'mission', 'objetivo', 'revista', 'journal', 'about', 'focus', 'pesquisa', 'research']):
                            texts.append(txt)
                
                if texts:
                    return " ".join(texts[:10])[:1000]
        except:
            continue
    return ""


def main():
    print("=" * 60)
    print("Enriquecimento de Perfil Editorial")
    print("=" * 60)
    
    # Faz backup
    if not os.path.exists(BACKUP_PATH):
        import shutil
        shutil.copy(CSV_PATH, BACKUP_PATH)
        print("Backup criado")
    
    # Lê CSV com latin-1
    df = pd.read_csv(CSV_PATH, sep=";", encoding="latin-1", on_bad_lines="skip")
    print(f"\nTotal registros: {len(df)}")
    print(f"Colunas: {len(df.columns)}")
    
    # Identifica colunas
    col_titulo = 0
    col_issn = 1  
    col_homepage = 2
    
    # Adiciona coluna Perfil_Editorial
    if "Perfil_Editorial" not in df.columns:
        df["Perfil_Editorial"] = ""
    
    col_idx_perfil = df.columns.get_loc("Perfil_Editorial")
    
    # Encontra registros vazios
    mask_vazio = df["Perfil_Editorial"].isna() | (df["Perfil_Editorial"].astype(str).str.strip().str.len() <= 10)
    indices = df[mask_vazio].index.tolist()
    
    print(f"Registros vazios: {len(indices)}")
    
    if not indices:
        print("Nada a atualizar!")
        return
    
    # Processa 10 periódicos
    batch = min(10, len(indices))
    success = 0
    
    print(f"\nProcessando {batch} periódicos...")
    
    for i, idx in enumerate(indices[:batch]):
        title = str(df.iat[idx, col_titulo])[:80]
        issn = str(df.iat[idx, col_issn]).strip()
        homepage = str(df.iat[idx, col_homepage]).strip()
        
        print(f"  [{i+1}] {title[:50]}...")
        
        # Tenta CrossRef
        perfil = fetch_crossref(issn)
        
        # Se não encontrar, tenta homepage
        if "não" in perfil.lower() or not perfil:
            perfil = fetch_from_homepage(homepage, title)
        
        if perfil and len(perfil) > 30:
            df.iat[idx, col_idx_perfil] = perfil[:1000]
            success += 1
            print(f"       ✓ Encontrado")
        else:
            df.iat[idx, col_idx_perfil] = "Informação não encontrada"
            print(f"       ✗ Não encontrado")
        
        time.sleep(0.5)
    
    # Salva com latin-1
    df.to_csv(CSV_PATH, index=False, encoding="latin-1", sep=";")
    
    print(f"\nConcluído! Sucesso: {success}/{batch}")
    print(f"Arquivo: {CSV_PATH}")


if __name__ == "__main__":
    main()
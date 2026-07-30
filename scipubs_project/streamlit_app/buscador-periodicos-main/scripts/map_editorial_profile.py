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
from typing import Optional

CSV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dados_new.csv")
OUTPUT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dados_new_atualizado.csv")


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
            # Aviso do publisher
            warning = message.get("warning", "")
            if warning and len(str(warning).strip()) > 10:
                parts.append(str(warning).strip())
            
            # Assuntos (toc)
            subjects = message.get("subjects", [])
            if subjects:
                subj_names = [s.get("name", "") for s in subjects if s.get("name")]
                if subj_names:
                    parts.append(f"Áreas: {', '.join(subj_names[:5])}")
                
            return " ".join(parts) if parts else None
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
        keywords = ['aim', 'scope', 'mission', 'objective', 'focus', 'about', 'journal']
        
        for p in soup.find_all(['p', 'div', 'span']):
            text = p.get_text(strip=True)
            if len(text) > 100 and any(kw in text.lower() for kw in keywords):
                if len(text) > 500:
                    text = text[:500] + "..."
                return text
        return None
    except Exception:
        return None


def main():
    print("=" * 60)
    print("Mapeamento de Perfil Editorial de Periódicos")
    print("=" * 60)
    
    # Detecta separator automaticamente
    with open(CSV_PATH, 'rb') as f:
        sample = f.read(1000)
        sep = ";" if sample.count(b";") > sample.count(b",") else ","
    
    # Lê CSV (usa latin-1 diretamente, pois o arquivo tem caracteres especiais)
    print(f"\nLendo {CSV_PATH}...")
    df = pd.read_csv(CSV_PATH, sep=sep, encoding="latin-1", on_bad_lines="skip")
    print(f"Total registros: {len(df)}")
    print(f"Colunas: {df.columns.tolist()[:5]}...")
    
    # Identifica colunas
    title_col = "Título da Revista"
    issn_col = "ISSN"
    homepage_col = "Homepage"
    aims_col = "Aims and Scope (translate)"
    
    # Adiciona coluna Perfil_Editorial
    df["Perfil_Editorial"] = ""
    
    # Preenche Perfil_Editorial com Aims and Scope existente (vetorizado)
    mask_exists = df[aims_col].notna() & (df[aims_col].astype(str).str.strip().str.len() > 20)
    df.loc[mask_exists, "Perfil_Editorial"] = df.loc[mask_exists, aims_col]
    existentes = mask_exists.sum()
    print(f"Com Aims and Scope: {existentes}")
    
    # Encontra registros vazios
    mask_vazio = df["Perfil_Editorial"].isna() | (df["Perfil_Editorial"].astype(str).str.strip().str.len() <= 10)
    indices = df[mask_vazio].index.tolist()
    total_buscar = len(indices)
    print(f"A buscar: {total_buscar}")
    
    if total_buscar == 0:
        df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")
        print("CSV salvo!")
        return
    
    # Processa apenas 10 para demonstração rápida
    demo_count = min(10, total_buscar)
    success = 0
    
    print(f"\nProcessando {demo_count} periódicos (demo)...")
    
    for i, idx in enumerate(indices[:demo_count]):
        issn = str(df.at[idx, issn_col]).strip()
        homepage = str(df.at[idx, homepage_col]).strip()
        title = str(df.at[idx, title_col]).strip()
        
        perfil = fetch_crossref(issn)
        
        if not perfil and homepage:
            perfil = fetch_from_homepage(homepage)
        
        if perfil:
            df.at[idx, "Perfil_Editorial"] = perfil[:500]
            success += 1
            print(f"  [{i+1}] OK: {title[:40]}...")
        else:
            df.at[idx, "Perfil_Editorial"] = "Informação não encontrada"
            print(f"  [{i+1}] Não encontrado: {title[:40]}...")
        
        time.sleep(0.2)
    
    # Salva (mantém o separator do original)
    df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig", sep=";")
    
    print("\n" + "=" * 60)
    print(f"RESUMO: Total={len(df)}, Existentes={existentes}, Demo={demo_count}, Sucesso={success}")
    print(f"CSV: {OUTPUT_PATH}")
    print("=" * 60)
    
    # Exibe exemplos
    print("\nExemplos:")
    samples = df[df["Perfil_Editorial"].notna() & (df["Perfil_Editorial"].str.len() > 50)].head(5)
    for idx, row in samples.iterrows():
        print(f"\n{row[title_col]}:")
        print(f"  {str(row['Perfil_Editorial'])[:300]}...")


if __name__ == "__main__":
    main()
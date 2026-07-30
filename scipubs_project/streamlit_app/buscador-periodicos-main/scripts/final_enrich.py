#!/usr/bin/env python3
"""
Script final para enriquecer Perfil Editorial no CSV original.
Processa URLs diretamente e adiciona informações encontradas.
"""

import os
import time
import csv
import requests
from bs4 import BeautifulSoup

CSV_PATH = "C:/Users/jquad/Documents/app-revista/dados_new.csv"
OUTPUT_PATH = "C:/Users/jquad/Documents/app-revista/dados_new.csv"

# Header do arquivo original
HEADER = [
    "Título da Revista", "ISSN", "Homepage", "Aims and Scope (translate)",
    "Grande Area", "Area do Conhecimento", "Subárea do Conhecimento", 
    "Indexador", "JIF", "Quartil JCR", "SJR", "SJR Best Quartile", "H index", "Índice h5",
    "Perfil_Editorial"  # Nova coluna
]

def fetch_profile(issn: str, homepage: str) -> str:
    """Obtém perfil usando CrossRef ou homepage"""
    
    # Tenta CrossRef
    if issn and len(issn.replace("-", "")) == 8:
        try:
            url = f"https://api.crossref.org/journals/{issn.replace('-', '')}"
            resp = requests.get(url, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                msg = data.get("message", {})
                parts = []
                if msg.get("publisher"):
                    parts.append(f"Editora: {msg['publisher']}")
                subs = msg.get("subjects", [])
                if subs:
                    names = [s.get("name", "") for s in subs[:5] if s.get("name")]
                    if names: parts.append(f"Áreas: {', '.join(names)}")
                if msg.get("description"):
                    parts.append(str(msg["description"])[:500])
                if parts: return " | ".join(parts)
        except:
            pass
    
    # Tenta homepage
    if homepage and homepage.startswith("http"):
        try:
            paths = ["/about", "/aims", "/scope", "/about-the-journal", "/aims-and-scope"]
            for p in paths:
                url = homepage.rstrip('/') + p
                resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    texts = []
                    for el in soup.find_all(['p', 'div'])[:20]:
                        txt = el.get_text(strip=True)
                        if 150 <= len(txt) <= 1000:
                            if any(k in txt.lower() for k in ['aim', 'scope', 'mission', 'about', 'focus', 'journal']):
                                texts.append(txt)
                    if texts: return " ".join(texts[:5])[:800]
        except:
            pass
    
    return "Informação não encontrada"


def main():
    print("=" * 60)
    print("Processamento de Perfil Editorial")
    print("=" * 60)
    
    # Lê CSV linha a linha (ignora encoding)
    rows = []
    with open(CSV_PATH, 'r', encoding='latin-1') as f:
        reader = csv.reader(f, delimiter=';')
        header = next(reader)
        print(f"Colunas originais: {len(header)}")
        
        for row in reader:
            # Garante 15 colunas
            while len(row) < 15:
                row.append("")
            rows.append(row)
    
    print(f"Total linhas: {len(rows)}")
    
    # Atualiza até 15 linhas para demonstração
    print("\nProcessando primeiras 15 linhas...")
    
    success = 0
    for i in range(min(15, len(rows))):
        title = str(rows[i][0])[:60]
        issn = str(rows[i][1]).strip()
        homepage = str(rows[i][2]).strip()
        
        print(f"  [{i+1}] {title}...")
        
        perfil = fetch_profile(issn, homepage)
        rows[i][14] = perfil  # Coluna Perfil_Editorial
        
        if "não encontrada" not in perfil.lower():
            success += 1
            print(f"       ✓")
        else:
            print(f"       ✗")
        
        time.sleep(0.4)
    
    # Salva
    with open(OUTPUT_PATH, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(HEADER)  # Novo header com Perfil_Editorial
        writer.writerows(rows)
    
    print(f"\nConcluído! {success}/15 perfis encontrados")
    print(f"Arquivo: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
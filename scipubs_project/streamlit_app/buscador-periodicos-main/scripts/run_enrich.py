#!/usr/bin/env python3
"""
Processa Perfil Editorial - versao ASCII
"""

import os
import time
import csv
import requests
from bs4 import BeautifulSoup

CSV_PATH = "C:/Users/jquad/Documents/app-revista/dados_new.csv"

# Header
NEW_HEADER = [
    "Título da Revista", "ISSN", "Homepage", "Aims and Scope (translate)",
    "Grande Area", "Area do Conhecimento", "Subárea do Conhecimento", 
    "Indexador", "JIF", "Quartil JCR", "SJR", "SJR Best Quartile", "H index", "Índice h5",
    "Perfil_Editorial"
]

def fetch_crossref(issn: str) -> str:
    """Busca na CrossRef API"""
    issn_clean = issn.replace("-", "")
    if len(issn_clean) != 8:
        return ""
    
    try:
        resp = requests.get(f"https://api.crossref.org/journals/{issn_clean}", timeout=8)
        if resp.status_code == 200:
            data = resp.json()
            msg = data.get("message", {})
            parts = []
            for key in ["publisher", "description"]:
                if msg.get(key):
                    parts.append(str(msg[key])[:400])
            subjects = msg.get("subjects", [])
            if subjects:
                names = [s.get("name", "") for s in subjects[:5] if s.get("name")]
                if names:
                    parts.append("Areas: " + ", ".join(names))
            return " | ".join(parts) if parts else ""
    except:
        pass
    return ""


def main():
    print("=" * 60)
    print("Perfil Editorial - Processamento")
    print("=" * 60)
    
    # Lê com csv reader (latin-1)
    with open(CSV_PATH, 'r', encoding='latin-1') as f:
        reader = csv.reader(f, delimiter=';')
        old_header = next(reader)
        print(f"Header original colunas: {len(old_header)}")
        
        rows = []
        for row in reader:
            # Garante 15 colunas
            while len(row) < 15:
                row.append("")
            rows.append(row)
    
    print(f"Total registros: {len(rows)}")
    
    # Processa 10 registros
    print("\nProcessando 10 primeiros...")
    
    for i in range(min(10, len(rows))):
        title = str(rows[i][0])
        issn = str(rows[i][1]).strip()
        homepage = str(rows[i][2]).strip()
        
        print(f"[{i+1}] {title[:50]}")
        
        # Busca
        perfil = fetch_crossref(issn)
        if perfil:
            print("    Encontrado via CrossRef")
        else:
            perfil = "Informacao nao encontrada"
            print("    Nao encontrado")
        
        rows[i][14] = perfil
        time.sleep(0.3)
    
    # Salva com utf-8-sig
    with open(CSV_PATH, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(NEW_HEADER)
        writer.writerows(rows)
    
    print("\nConcluido!")
    print(f"Arquivo salvo: {CSV_PATH}")


if __name__ == "__main__":
    main()
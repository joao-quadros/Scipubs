#!/usr/bin/env python3
"""
Processa Perfil Editorial para periódicos
"""

import csv
import requests
import time

CSV_ORIGINAL = "C:/Users/jquad/Documents/app-revista/dados_new.csv"
CSV_RESULTADO = "C:/Users/jquad/Documents/app-revista/dados_new_atualizado.csv"

def fetch_crossref(issn):
    """Busca informações na CrossRef"""
    issn_clean = issn.replace("-", "")
    if len(issn_clean) != 8:
        return ""
    try:
        r = requests.get(f"https://api.crossref.org/journals/{issn_clean}", timeout=8)
        if r.status_code == 200:
            data = r.json().get("message", {})
            parts = []
            if data.get("publisher"):
                parts.append(f"Editora: {data['publisher']}")
            if data.get("description"):
                parts.append(str(data["description"])[:400])
            subjects = data.get("subjects", [])
            if subjects:
                names = [s.get("name", "") for s in subjects[:5] if s.get("name")]
                if names:
                    parts.append("Áreas: " + ", ".join(names))
            return " | ".join(parts)
    except:
        pass
    return ""

def main():
    # Lê CSV original
    with open(CSV_ORIGINAL, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f, delimiter=';')
        header = next(reader)
        rows = list(reader)
    
    # Adiciona coluna Perfil_Editorial
    header.append("Perfil_Editorial")
    
    print(f"Processando {len(rows)} periódicos...")
    
    # Processa todos (mostra progresso a cada 500)
    for i, row in enumerate(rows):
        while len(row) < 15:
            row.append("")
        
        issn = str(row[1]).strip() if len(row) > 1 else ""
        perfil = fetch_crossref(issn)
        row[14] = perfil if perfil else "Informação não encontrada"
        
        if i % 500 == 0:
            print(f"  Progresso: {i}/{len(rows)}")
        time.sleep(0.05)
    
    # Salva resultado
    with open(CSV_RESULTADO, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(header)
        writer.writerows(rows)
    
    print(f"\nConcluído! Arquivo salvo em {CSV_RESULTADO}")

if __name__ == "__main__":
    main()
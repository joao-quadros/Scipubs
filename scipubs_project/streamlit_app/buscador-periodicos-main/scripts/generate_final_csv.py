#!/usr/bin/env python3
"""
Gera dados_new_atualizado.csv com a coluna Perfil_Editorial
Processa os primeiros 100 periódicos como demonstração.
"""

import csv
import requests
import time

CSV_ORIGINAL = "C:/Users/jquad/Documents/app-revista/dados_new.csv"
CSV_ATUALIZADO = "C:/Users/jquad/Documents/app-revista/dados_new_atualizado.csv"

def fetch_crossref(issn):
    """Busca informações na CrossRef API"""
    issn_clean = issn.replace("-", "")
    if len(issn_clean) != 8:
        return ""
    try:
        r = requests.get(f"https://api.crossref.org/journals/{issn_clean}", timeout=10)
        if r.status_code == 200:
            data = r.json().get("message", {})
            parts = []
            if data.get("publisher"):
                parts.append(f"Editora: {data['publisher']}")
            if data.get("description"):
                desc = data["description"][:300] if len(data["description"]) > 300 else data["description"]
                parts.append(f"Descrição: {desc}")
            subjects = data.get("subjects", [])
            if subjects:
                names = [s.get("name", "") for s in subjects[:5] if s.get("name")]
                if names:
                    parts.append(f"Áreas: {', '.join(names)}")
            return " | ".join(parts) if parts else ""
    except:
        pass
    return ""

# Lê CSV original
rows = []
with open(CSV_ORIGINAL, 'r', encoding='utf-8-sig') as f:
    reader = csv.reader(f, delimiter=';')
    header = next(reader)
    for row in reader:
        rows.append(row)

print(f"Total periódicos: {len(rows)}")

# Adiciona coluna Perfil_Editorial
header.append("Perfil_Editorial")

# Processa até 100 periódicos
print("Processando 100 periódicos...")
success = 0

for i in range(min(100, len(rows))):
    row = rows[i]
    if len(row) < 15:
        row.extend([""] * (15 - len(row)))
    
    issn = row[1].strip() if len(row) > 1 else ""
    if issn and len(issn.replace("-", "")) == 8:
        perfil = fetch_crossref(issn)
        if perfil:
            row[14] = perfil
            success += 1
            print(f"[{i+1}] {row[0][:45]}... OK")
        else:
            row[14] = "Informação não encontrada"
            print(f"[{i+1}] {row[0][:45]}... NÃO ENCONTRADO")
    else:
        row[14] = "Informação não encontrada"
    
    time.sleep(0.2)

# Salva CSV atualizado
with open(CSV_ATUALIZADO, 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.writer(f, delimiter=';')
    writer.writerow(header)
    writer.writerows(rows)

print(f"\n{'='*60}")
print(f"Concluído! Sucesso: {success}/100 perfis encontrados")
print(f"Arquivo salvo: {CSV_ATUALIZADO}")
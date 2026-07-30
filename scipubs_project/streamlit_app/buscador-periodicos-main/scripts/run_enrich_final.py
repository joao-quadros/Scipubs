#!/usr/bin/env python3
import csv
import requests
import time

CSV_PATH = "C:/Users/jquad/Documents/app-revista/dados_new.csv"

# Header com Perfil_Editorial
HEADER = [
    "Título da Revista", "ISSN", "Homepage", "Aims and Scope (translate)",
    "Grande Area", "Area do Conhecimento", "Subárea do Conhecimento", 
    "Indexador", "JIF", "Quartil JCR", "SJR", "SJR Best Quartile", "H index", "Índice h5",
    "Perfil_Editorial"
]

def fetch_crossref(issn):
    issn_clean = issn.replace("-", "")
    if len(issn_clean) != 8:
        return ""
    try:
        r = requests.get(f"https://api.crossref.org/journals/{issn_clean}", timeout=8)
        if r.status_code == 200:
            data = r.json().get("message", {})
            parts = []
            if data.get("publisher"):
                parts.append("Editora: " + data["publisher"])
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

# Lê com latin-1
rows = []
with open(CSV_PATH, 'r', encoding='latin-1') as f:
    reader = csv.reader(f, delimiter=';')
    next(reader)  # pula header
    for row in reader:
        rows.append(row)

print("Processando", len(rows), "registros...")

for i, row in enumerate(rows[:50]):  # Processa 50 primeiros
    issn = row[1] if len(row) > 1 else ""
    perfil = fetch_crossref(issn)
    if len(row) < 15:
        row.extend([""] * (15 - len(row)))
    row[14] = perfil if perfil else "Informação não encontrada"
    print(i+1, "-", row[0][:40], "OK" if perfil else "NÃO ENCONTRADO")
    time.sleep(0.2)

# Salva
with open(CSV_PATH, 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.writer(f, delimiter=';')
    writer.writerow(HEADER)
    writer.writerows(rows)

print("Concluído!")
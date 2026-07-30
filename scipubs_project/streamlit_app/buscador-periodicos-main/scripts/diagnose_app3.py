import re

with open('app(3).py', encoding='utf-8', errors='ignore') as f:
    app_lines = f.readlines()

print(f"Total de linhas em app(3).py: {len(app_lines)}")

# Localizar onde a Aba 2 / Recomendador Inteligente é renderizada
start_aba2 = None
for i, line in enumerate(app_lines):
    if "Recomendação Temática com Inteligência Artificial" in line or "Recomendador Inteligente" in line or "recommend(" in line:
        print(f"Linha {i+1}: {line.strip()[:100]}")

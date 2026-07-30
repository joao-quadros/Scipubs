"""
Script de Recodificação de Áreas do Conhecimento (Padrão CNPq)
Este script analisa as colunas 'Grande Área', 'Área do Conhecimento' e 'Categoria' no dados.csv
e recodifica a coluna 'Grande Área' estritamente para as 9 Grandes Áreas Oficiais do CNPq em Português.
"""

import os
import sys
import pandas as pd
import unicodedata

# Diretório base
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(BASE_DIR, "dados.csv")

def remover_acentos(texto):
    if not texto or pd.isna(texto):
        return ""
    texto_str = str(texto)
    s = unicodedata.normalize('NFD', texto_str)
    return ''.join(c for c in s if unicodedata.category(c) != 'Mn').lower().strip()

def classificar_cnpq(row):
    # Coleta todos os metadados de área e categoria da linha
    ga_orig = str(row.get("Grande Área", row.get("Grande Area", "")))
    cat_orig = str(row.get("Categoria", ""))
    area_orig = str(row.get("Área do Conhecimento", row.get("Área de Conhecimento", "")))
    title_orig = str(row.get("Título da Revista", row.get("title", "")))
    
    combined_text = remover_acentos(f"{ga_orig} {cat_orig} {area_orig} {title_orig}")
    
    areas_encontradas = set()
    
    # 1. Ciências Exatas e da Terra (Código CNPq 1000000X)
    exatas_kw = [
        "exact and earth", "exatas e da terra", "mathematics", "matematica", "computer", "computacao", 
        "astronomy", "astronomia", "physics", "fisica", "chemistry", "quimica", "geosciences", "geociencias",
        "earth and planetary", "geology", "geologia", "oceanography", "oceanografia", "nanoscience",
        "materials science", "analytical", "logic", "statistics", "estatistica"
    ]
    if any(kw in combined_text for kw in exatas_kw):
        areas_encontradas.add("Ciências Exatas e da Terra")
        
    # 2. Ciências Biológicas (Código CNPq 2000000X)
    bio_kw = [
        "biological sciences", "ciencias biologicas", "biology", "biologia", "genetics", "genetica", 
        "botany", "botanica", "zoology", "zoologia", "ecology", "ecologia", "biochemistry", "bioquimica", 
        "biophysics", "biofisica", "pharmacology", "farmacologia", "immunology", "imunologia", 
        "microbiology", "microbiologia", "parasitology", "parasitologia", "neurosciences", "neurociencia", 
        "toxicology", "biotechnology"
    ]
    if any(kw in combined_text for kw in bio_kw):
        areas_encontradas.add("Ciências Biológicas")
        
    # 3. Engenharias (Código CNPq 3000000X)
    eng_kw = [
        "engineering", "engenharia", "engenharias", "civil construction", "electrical and electronic", 
        "mechanical engineering", "chemical engineering", "sanitary", "nuclear engineering", 
        "transportation", "aerospace", "biomedical engineering", "manufacturing", "robotics", "textiles"
    ]
    if any(kw in combined_text for kw in eng_kw):
        areas_encontradas.add("Engenharias")
        
    # 4. Ciências da Saúde (Código CNPq 4000000X)
    saude_kw = [
        "health sciences", "ciencias da saude", "medicine", "medicina", "dentistry", "odontologia", 
        "pharmacy", "farmacia", "nursing", "enfermagem", "nutrition", "nutricao", "public health", 
        "saude publica", "speech therapy", "fonoaudiologia", "physical therapy", "fisioterapia", 
        "physical education", "educacao fisica", "gastroenterology", "clinical", "radiology", 
        "endocrinology", "anesthesiology", "surgery", "pediatrics", "oncology", "dermatology", 
        "cardiology", "neurology", "psychiatry", "psiquiatria"
    ]
    if any(kw in combined_text for kw in saude_kw):
        areas_encontradas.add("Ciências da Saúde")
        
    # 5. Ciências Agrárias (Código CNPq 5000000X)
    agraria_kw = [
        "agricultural sciences", "ciencias agrarias", "agronomy", "agronomia", "forestry", "florestal", 
        "agricultural engineering", "animal science", "zootecnia", "veterinary", 
        "fisheries", "pesca", "aquaculture", "aquicultura", "food science", "entomology"
    ]
    if any(kw in combined_text for kw in agraria_kw):
        areas_encontradas.add("Ciências Agrárias")
        
    # 6. Ciências Sociais Aplicadas (Código CNPq 6000000X)
    soc_kw = [
        "applied social", "ciencias sociais aplicadas", "law", "direito", "administration", "administracao", 
        "management", "business", "economics", "economia", "architecture", "arquitetura", "urbanism", 
        "urbanismo", "demography", "demografia", "information science", "ciencia da informacao", 
        "library science", "biblioteconomia", "museology", "museologia", "communication", "comunicacao", 
        "journalism", "jornalismo", "social work", "servico social", "tourism", "turismo", "finance", 
        "accounting", "contabilidade"
    ]
    if any(kw in combined_text for kw in soc_kw):
        areas_encontradas.add("Ciências Sociais Aplicadas")
        
    # 7. Ciências Humanas (Código CNPq 7000000X)
    hum_kw = [
        "humanities", "ciencias humanas", "philosophy", "filosofia", "sociology", "sociologia", 
        "anthropology", "antropologia", "archaeology", "arqueologia", "history", "historia", 
        "geography", "geografia", "psychology", "psicologia", "education", "educacao", "pedagogy", 
        "political science", "ciencia politica", "theology", "teologia", "ethics"
    ]
    if any(kw in combined_text for kw in hum_kw):
        areas_encontradas.add("Ciências Humanas")
        
    # 8. Linguística, Letras e Artes (Código CNPq 8000000X)
    artes_kw = [
        "letters and arts", "linguistics", "linguistica", "linguistica, letras e artes", "language", 
        "lingua", "literature", "literatura", "letters", "letras", "arts", "artes", "music", "musica", 
        "musicology", "musicologia", "visual arts", "performing arts", "theatre", "teatro", "cinema"
    ]
    if any(kw in combined_text for kw in artes_kw):
        areas_encontradas.add("Linguística, Letras e Artes")
        
    # Ordem de prioridade e saída
    ordem_cnpq = [
        "Ciências Exatas e da Terra",
        "Ciências Biológicas",
        "Engenharias",
        "Ciências da Saúde",
        "Ciências Agrárias",
        "Ciências Sociais Aplicadas",
        "Ciências Humanas",
        "Linguística, Letras e Artes"
    ]
    
    if not areas_encontradas:
        return "Outras / Não Classificado"
        
    areas_ordenadas = [a for a in ordem_cnpq if a in areas_encontradas]
    return ", ".join(areas_ordenadas)

def recodificar():
    print(f"Lendo base de dados em: {CSV_PATH}...")
    df = pd.read_csv(CSV_PATH, low_memory=False)
    
    col_ga = "Grande Área" if "Grande Área" in df.columns else "Grande Area"
    
    print("Aplicando algoritmo de recodificação CNPq...")
    df[col_ga] = df.apply(classificar_cnpq, axis=1)
    
    print("Salvando base de dados atualizada...")
    df.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")
    
    print("\n--- DISTRIBUIÇÃO DE FREQUÊNCIA APÓS RECODIFICAÇÃO CNPQ ---")
    print(df[col_ga].value_counts().head(20))
    print("\nRecodificação concluída com sucesso!")

if __name__ == "__main__":
    recodificar()

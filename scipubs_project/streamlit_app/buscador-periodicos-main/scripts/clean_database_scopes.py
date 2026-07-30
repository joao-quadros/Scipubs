import os
import pandas as pd
import unicodedata

BASE_DIR = r"C:\Users\jquad\Documents\app-revista"
CSV_PATH = os.path.join(BASE_DIR, "dados.csv")

def normalize_text(text):
    if not isinstance(text, str):
        return ""
    text_norm = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII')
    return text_norm.lower()

def is_boilerplate(text):
    if pd.isna(text) or not isinstance(text, str) or not text.strip():
        return True
    
    text_norm = normalize_text(text)
    
    # 1. Mensagens comemorativas específicas
    if "trinta anos" in text_norm and "archives of veterinary" in text_norm:
        return True
    if "marco cronologico" in text_norm or "aniversario da" in text_norm or "aniversario de" in text_norm:
        return True
        
    # 2. Palavras-chave de submissão burocrática pura
    boilerplate_indicators = [
        "recibe trabajos para publicacion",
        "normas de publicacion",
        "normas de publicacao",
        "directrices para autores",
        "instrucoes para autores",
        "instrucciones para autores",
        "guidelines for authors",
        "instructions for authors",
        "articulos originales, casos clinicos",
        "artigos originais, casos clinicos",
        "originales, casos clinicos y revision",
        "casos clinicos, notas tecnicas",
        "cartas al editor y revisiones",
        "licencia creative commons",
        "licenca creative commons",
        "bajo una licencia",
        "todos los derechos reservados",
        "todos os direitos reservados",
        "all rights reserved",
        "propiedad intelectual de nuestra asociacion",
        "publicacion trimestral que edita trabajos",
        "revista digital gratuita, sujeta a revision por pares",
        "revista de filologia de la universidad de la laguna es una publicacion"
    ]
    
    for ind in boilerplate_indicators:
        if ind in text_norm:
            return True
            
    # 3. Se for muito curto e contiver palavras de publicação genéricas
    if len(text_norm) < 400:
        generic_words = ["revista", "publicacion", "publicacao", "artigo", "articulo", "editor", "submissao", "envio", "issn"]
        match_count = sum(1 for w in generic_words if w in text_norm)
        if match_count >= 3:
            return True
            
    return False

def clean_database():
    print("Carregando base de dados...")
    df = pd.read_csv(CSV_PATH)
    col_scope = "Aims and Scope"
    
    print("Iniciando limpeza dos escopos...")
    cleaned_count = 0
    
    for idx, row in df.iterrows():
        scope = row[col_scope]
        if not pd.isna(scope) and str(scope).strip() != "":
            if is_boilerplate(scope):
                df.at[idx, col_scope] = ""
                cleaned_count += 1
                
    print(f"Limpeza concluída! Total de escopos limpos: {cleaned_count} de {len(df)}")
    
    # Salva base atualizada
    df.to_csv(CSV_PATH, index=False)
    print("Base de dados 'dados.csv' atualizada com sucesso!")

if __name__ == "__main__":
    clean_database()

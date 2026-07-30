import requests
import urllib.parse

def translate_to_academic_english(text):
    """Traduz textos em português/espanhol/outros idiomas para Inglês Acadêmico via Google GTX API."""
    if not text or str(text).strip() in ["-", "", "nan", "None"]:
        return ""
        
    text_clean = str(text).strip()
    
    # Se o texto já for majoritariamente em inglês, retorna diretamente
    text_low = text_clean.lower()
    english_words = ["the ", " journal", "publishes ", "peer-reviewed", "research", "aims to", "focuses on", "scope of"]
    if sum(1 for w in english_words if w in text_low) >= 2:
        return text_clean

    try:
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=en&dt=t&q={urllib.parse.quote(text_clean)}"
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            res_json = r.json()
            sentences = res_json[0]
            translated_text = "".join([s[0] for s in sentences if s and len(s) > 0 and s[0]])
            return translated_text.strip()
    except Exception as e:
        print(f"Erro na tradução: {e}")
    return text_clean

# Teste com texto da Revista de Saúde Pública e 1616 Anuario
sample_pt = "1616: Anuario de Literatura Comparada, revista-anuario de la Sociedad Española de Literatura General y Comparada, constituye el órgano de expresión de dicha sociedad científica y publica contribuciones relativas a esa disciplina."
sample_pt2 = "Publicar e disseminar produtos do trabalho científico que sejam relevantes para a Saúde Pública."

print("Original 1:", sample_pt)
print("Traduzido 1:", translate_to_academic_english(sample_pt))
print("\nOriginal 2:", sample_pt2)
print("Traduzido 2:", translate_to_academic_english(sample_pt2))

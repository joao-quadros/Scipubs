import requests
from bs4 import BeautifulSoup
import re
import urllib.parse

# Teste: Google Scholar Citation Venues Search para Revista de Saúde Pública
journal_name = "Revista de Saude Publica"
url_gs = f"https://scholar.google.com/citations?hl=pt-BR&view_op=search_venues&vq={urllib.parse.quote(journal_name)}&btnG="

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

try:
    r = requests.get(url_gs, headers=headers, timeout=6)
    print("GS Venues status:", r.status_code)
    soup = BeautifulSoup(r.text, 'html.parser')
    
    # Tabela do Google Scholar para Venues traz: Posição | Periódico | Índice h5 | Mediana h5
    table = soup.find('table', id='gsc_mp_table') or soup.find('table')
    if table:
        for tr in table.find_all('tr'):
            tds = [td.text.strip() for td in tr.find_all(['td', 'th'])]
            if tds:
                print("Linha Tabela Scholar:", tds)
except Exception as e:
    print("Erro Scholar:", e)

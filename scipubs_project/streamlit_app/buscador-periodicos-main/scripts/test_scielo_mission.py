import sys
sys.path.append('.')
from scripts.enrich_dados_2 import scrape_homepage_aims

url = "https://www.scielo.br/j/rsp/"
res = scrape_homepage_aims(url)
print("--- TESTE EXTRAÇÃO SCIELO (REVISTA SAÚDE PÚBLICA) ---")
print(res)

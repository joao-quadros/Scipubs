import sys
sys.path.append('.')
import pandas as pd
from scripts.enrich_dados_2 import scrape_homepage_aims, fetch_openalex_aims

df = pd.read_csv('dados_2.csv', sep=';', encoding='utf-8-sig', low_memory=False)
col_title = df.columns[0]

for idx in range(10):
    row = df.iloc[idx]
    title = row[col_title]
    issn = row.get("ISSN", "")
    hp = row.get("Homepage", "")
    
    print(f"\n--- Row {idx}: {title} ---")
    print(f"ISSN: {issn} | HP: {hp}")
    
    sc = scrape_homepage_aims(hp)
    print(f"Scraped Scope: '{sc[:150]}...' (Len: {len(sc)})")
    
    oa = fetch_openalex_aims(issn, title)
    print(f"OpenAlex Scope: '{oa}'")

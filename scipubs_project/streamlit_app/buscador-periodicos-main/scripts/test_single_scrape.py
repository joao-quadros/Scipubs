import requests
from bs4 import BeautifulSoup
import re

urls = [
    ("1616", "http://revistas.usal.es/index.php/1616_Anuario_Literatura_Comp/index"),
    ("Nordic", "https://septentrio.uit.no/index.php/1700"),
    ("2D Materials", "http://iopscience.iop.org/2053-1583"),
    ("3 Biotech", "https://www.springer.com/journal/13205"),
    ("3D Med", "https://threedmedprint.biomedcentral.com/"),
]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,pt-BR;q=0.8"
}

for name, url in urls:
    print(f"\n--- Testing {name}: {url} ---")
    try:
        r = requests.get(url, headers=headers, timeout=8, allow_redirects=True)
        print(f"Status: {r.status_code} | Final URL: {r.url}")
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # Meta description
        meta = soup.find('meta', attrs={'name': re.compile('description', re.I)}) or soup.find('meta', property='og:description')
        if meta and meta.get('content'):
            print(f"Meta Desc: {meta.get('content')[:200]}...")
            
        # OJS specific check (common in academic journals!)
        # OJS usually has sidebar block "About The Journal" or div class "journal-summary" / "description" / "about"
        ojs_summary = soup.find('div', class_=re.compile(r'journal-summary|homepage-about|about|description', re.I))
        if ojs_summary:
            print(f"OJS Summary found: {ojs_summary.text.strip()[:200]}...")
            
        # Check paragraphs
        ps = [p.text.strip() for p in soup.find_all('p') if len(p.text.strip()) > 40]
        print(f"Total long paragraphs found: {len(ps)}")
        if ps:
            print(f"First P: {ps[0][:150]}...")
            
    except Exception as e:
        print(f"Error: {e}")

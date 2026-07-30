import urllib.request
import urllib.parse
import ssl
import re
from bs4 import BeautifulSoup

ctx = ssl._create_unverified_context()

def search_yahoo(title, issn):
    query = f"{title} journal ISSN {issn} official website"
    print(f"Querying Yahoo: {query}")
    params = urllib.parse.urlencode({'p': query})
    url = f'https://search.yahoo.com/search?{params}'
    
    req = urllib.request.Request(
        url,
        headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
        }
    )
    
    blocklist = [
        'yahoo.com', 'yimg.com', 'portal.issn.org', 'wikipedia.org', 'wikidata.org',
        'facebook.com', 'twitter.com', 'linkedin.com', 'youtube.com', 'instagram.com',
        'researchgate.net', 'academia.edu', 'scopus.com', 'webofscience.com', 'crossref.org',
        'openalex.org', 'google.com'
    ]
    
    try:
        with urllib.request.urlopen(req, context=ctx) as r:
            html = r.read().decode('utf-8')
            
        soup = BeautifulSoup(html, 'html.parser')
        links = []
        for a in soup.find_all('a'):
            href = a.get('href')
            if href and 'r.search.yahoo.com' in href:
                m = re.search(r'/RU=(.+?)/RK=', href)
                if m:
                    decoded = urllib.parse.unquote(m.group(1))
                    links.append(decoded)
        
        filtered_links = []
        for link in links:
            is_blocked = False
            for domain in blocklist:
                if domain in link.lower():
                    is_blocked = True
                    break
            if not is_blocked:
                filtered_links.append(link)
                
        print(f"  All links found: {len(links)}")
        print(f"  Filtered links: {filtered_links[:3]}")
        if filtered_links:
            return filtered_links[0]
    except Exception as e:
        print(f"  Error: {e}")
    return None

test_cases = [
    ("ACM Transactions on Computing Education", "1946-6226"),
    ("ACTA BALNEOLOGICA", "2082-1867")
]

for title, issn in test_cases:
    homepage = search_yahoo(title, issn)
    print(f"Result Homepage: {homepage}")
    print("-" * 50)

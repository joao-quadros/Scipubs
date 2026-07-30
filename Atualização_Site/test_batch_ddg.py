import urllib.request
import urllib.parse
import ssl
import re
import time
from bs4 import BeautifulSoup

ctx = ssl._create_unverified_context()

def search_ddg_lite(title, issn):
    query = f"{title} journal ISSN {issn} official website"
    print(f"Querying: {query}")
    url = 'https://lite.duckduckgo.com/lite/'
    data = urllib.parse.urlencode({'q': query}).encode('utf-8')
    
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
    )
    
    blocklist = [
        'duckduckgo.com',
        'portal.issn.org',
        'wikipedia.org',
        'wikidata.org',
        'facebook.com',
        'twitter.com',
        'linkedin.com',
        'youtube.com',
        'instagram.com',
        'researchgate.net',
        'academia.edu',
        'scopus.com',
        'webofscience.com',
        'crossref.org',
        'openalex.org',
        'google.com'
    ]
    
    try:
        with urllib.request.urlopen(req, context=ctx) as response:
            html = response.read().decode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find result links
            links = []
            for a in soup.find_all('a', class_='result-link'):
                href = a.get('href')
                if href and href.startswith('http'):
                    links.append(href)
            
            # If no result-link class is found, fallback to any external links starting with http
            if not links:
                for a in soup.find_all('a'):
                    href = a.get('href')
                    if href and href.startswith('http') and not any(d in href for d in ['duckduckgo.com', '/']):
                        links.append(href)
            
            # Filter links by blocklist
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
            elif links:
                # If everything was blocked, maybe return the first link anyway (or not?)
                # The prompt says: "Parse the first result link that is external (not internal to DuckDuckGo, and not a portal like portal.issn.org or wikipedia.org if possible)."
                # So if possible, avoid them. If absolutely no other link exists, we can return the first link that is external,
                # but let's check if the first link is portal/wikipedia.
                # Actually, let's look at the first non-duckduckgo link that doesn't contain portal.issn.org or wikipedia.org.
                # Let's write code that prefers non-portal, non-wikipedia, non-social media.
                pass
    except Exception as e:
        print(f"  Error querying: {e}")
    return None

test_cases = [
    ("A + U-Architecture and Urbanism", "0389-9160"),
    ("A/Z ITU Journal of the Faculty of Architecture", "2564-7474"),
    ("ACM Transactions on Computing Education", "1946-6226"),
    ("ACTA BALNEOLOGICA", "2082-1867")
]

for title, issn in test_cases:
    homepage = search_ddg_lite(title, issn)
    print(f"Result Homepage: {homepage}")
    print("-" * 50)
    time.sleep(2)

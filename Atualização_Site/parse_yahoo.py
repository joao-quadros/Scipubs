from bs4 import BeautifulSoup
import urllib.request
import urllib.parse
import ssl
import re

ctx = ssl._create_unverified_context()

def parse():
    query = 'AEU-Archiv fur Elektronik und Ubertragungstechnik journal ISSN 0001-1096 official website'
    params = urllib.parse.urlencode({'p': query})
    url = f'https://search.yahoo.com/search?{params}'
    
    req = urllib.request.Request(
        url,
        headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
        }
    )
    with urllib.request.urlopen(req, context=ctx) as r:
        html = r.read().decode('utf-8')
    
    soup = BeautifulSoup(html, 'html.parser')
    for a in soup.find_all('a'):
        href = a.get('href')
        text = a.get_text(strip=True)
        if href and 'r.search.yahoo.com' in href:
            # Match RU=... up to /RK= or similar
            m = re.search(r'/RU=(.+?)/RK=', href)
            if m:
                encoded_url = m.group(1)
                original_url = urllib.parse.unquote(encoded_url)
                print(f"Text: {text[:40]:<40} | Decoded URL: {original_url}")

if __name__ == '__main__':
    parse()

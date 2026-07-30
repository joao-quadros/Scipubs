import urllib.request
import urllib.parse
import ssl
from bs4 import BeautifulSoup

ctx = ssl._create_unverified_context()

def test_yahoo():
    query = 'AEU-Archiv fur Elektronik und Ubertragungstechnik journal ISSN 0001-1096 official website'
    params = urllib.parse.urlencode({'p': query})
    url = f'https://search.yahoo.com/search?{params}'
    print(f"Querying Yahoo: {url}")
    
    req = urllib.request.Request(
        url,
        headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5'
        }
    )
    try:
        with urllib.request.urlopen(req, context=ctx) as r:
            html = r.read().decode('utf-8')
            print("HTML Length:", len(html))
            if "captcha" in html.lower() or "robot" in html.lower() or "unusual activity" in html.lower():
                print("--- BLOCKED BY CAPTCHA ---")
            else:
                soup = BeautifulSoup(html, 'html.parser')
                # Yahoo search results usually have class "d-flex ALi" or similar, or <a> with class "thUmbs"
                # Let's just extract all external links
                links = []
                for a in soup.find_all('a'):
                    href = a.get('href')
                    if href and href.startswith('http') and not any(d in href for d in ['yahoo.com', 'yimg.com']):
                        links.append(href)
                print("--- SUCCESS ---")
                print("Found links count:", len(links))
                for link in links[:5]:
                    print("  ", link)
    except Exception as e:
        print("Error:", e)

if __name__ == '__main__':
    test_yahoo()

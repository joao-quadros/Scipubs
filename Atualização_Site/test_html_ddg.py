import urllib.request
import urllib.parse
import ssl
from bs4 import BeautifulSoup
import time

ctx = ssl._create_unverified_context()

def test_html(title, issn):
    query = f"{title} journal ISSN {issn} official website"
    print(f"Querying HTML DDG: {query}")
    params = urllib.parse.urlencode({'q': query})
    url = f'https://html.duckduckgo.com/html/?{params}'
    
    req = urllib.request.Request(
        url,
        headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5'
        }
    )
    try:
        with urllib.request.urlopen(req, context=ctx) as response:
            html = response.read().decode('utf-8')
            print("HTML Length:", len(html))
            if "captcha" in html.lower() or "robot" in html.lower() or "human" in html.lower() or "unusual traffic" in html.lower():
                print("--- BOT DETECTION DETECTED ---")
            else:
                soup = BeautifulSoup(html, 'html.parser')
                links = []
                # In html version, links have class result__url or similar
                for a in soup.find_all('a', class_='result__url'):
                    href = a.get('href')
                    if href:
                        links.append(href)
                print("--- SUCCESS ---")
                print("Links found:", len(links))
                for link in links[:3]:
                    print("  ", link)
    except Exception as e:
        print("Error:", e)

test_html("ACM Transactions on Computing Education", "1946-6226")
time.sleep(2)
test_html("ACTA BALNEOLOGICA", "2082-1867")

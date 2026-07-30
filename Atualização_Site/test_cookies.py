import urllib.request
import urllib.parse
import ssl
from bs4 import BeautifulSoup
import time

ctx = ssl._create_unverified_context()

def test_session():
    # Build opener with cookie handling
    cookie_processor = urllib.request.HTTPCookieProcessor()
    opener = urllib.request.build_opener(cookie_processor)
    urllib.request.install_opener(opener)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'https://lite.duckduckgo.com/lite/'
    }
    
    # Step 1: GET homepage to establish cookies
    print("Step 1: GET homepage...")
    req_home = urllib.request.Request('https://lite.duckduckgo.com/lite/', headers=headers)
    try:
        with urllib.request.urlopen(req_home, context=ctx) as r:
            html_home = r.read().decode('utf-8')
            print("Homepage loaded. Length:", len(html_home))
            # print("Cookies:", cookie_processor.cookiejar)
    except Exception as e:
        print("GET failed:", e)
        return

    # Step 2: POST query
    query = 'AEU-Archiv fur Elektronik und Ubertragungstechnik journal ISSN 0001-1096 official website'
    print(f"Step 2: Searching: '{query}'...")
    data = urllib.parse.urlencode({'q': query}).encode('utf-8')
    
    req_search = urllib.request.Request(
        'https://lite.duckduckgo.com/lite/',
        data=data,
        headers={
            **headers,
            'Content-Type': 'application/x-www-form-urlencoded'
        }
    )
    
    try:
        with urllib.request.urlopen(req_search, context=ctx) as r:
            html = r.read().decode('utf-8')
            print("Search result length:", len(html))
            if "captcha" in html.lower() or "robot" in html.lower() or "human" in html.lower():
                print("--- STILL BLOCKED BY CAPTCHA ---")
            else:
                soup = BeautifulSoup(html, 'html.parser')
                links = []
                for a in soup.find_all('a', class_='result-link'):
                    href = a.get('href')
                    if href:
                        links.append(href)
                print("--- SUCCESS ---")
                print("Found links:", len(links))
                for link in links[:3]:
                    print("  ", link)
    except Exception as e:
        print("POST failed:", e)

if __name__ == '__main__':
    test_session()

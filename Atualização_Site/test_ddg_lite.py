import urllib.request
import urllib.parse
import re
import ssl

ctx = ssl._create_unverified_context()

def search_ddg_lite(query):
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
    
    try:
        with urllib.request.urlopen(req, context=ctx) as response:
            html = response.read().decode('utf-8')
            # Let's find links in the HTML
            # DuckDuckGo Lite results links look like:
            # <a class="result-link" href="URL">...</a>
            # or in general, look for hrefs
            print("HTML Length:", len(html))
            
            # Simple regex to find external links in result list
            # DDG Lite results are inside a table/form
            # Let's search for href patterns
            links = re.findall(r'href="([^"]+)"', html)
            external_links = []
            for link in links:
                # Filter out DDG internal links
                if not link.startswith('/') and not 'duckduckgo.com' in link and link.startswith('http'):
                    external_links.append(link)
            return external_links
    except Exception as e:
        print("Error:", e)
    return []

query = '3D Printing and Additive Manufacturing journal ISSN 2329-7662 official website'
print(f"Searching for: '{query}'")
results = search_ddg_lite(query)
print("Top links found:")
for link in results[:10]:
    print(link)

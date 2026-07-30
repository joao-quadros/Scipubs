import urllib.request
import urllib.parse
import json
import ssl

ctx = ssl._create_unverified_context()
issn = '2053-1583' # 2D Materials
url = f'https://api.crossref.org/journals/{issn}'

req = urllib.request.Request(
    url,
    headers={'User-Agent': 'BuscadorPeriodicosAutobuild/1.0 (mailto:jquad@example.com)'}
)

try:
    with urllib.request.urlopen(req, context=ctx) as response:
        data = json.loads(response.read().decode('utf-8'))
        print(json.dumps(data, indent=2))
except Exception as e:
    print("Error:", e)

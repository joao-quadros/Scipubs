import urllib.request
import urllib.parse
import json
import ssl

ctx = ssl._create_unverified_context()
url = 'https://api.openalex.org/sources?filter=issn:2329-7662&mailto=jquad@example.com'

req = urllib.request.Request(
    url,
    headers={'User-Agent': 'BuscadorPeriodicosAutobuild/1.0 (mailto:jquad@example.com)'}
)

try:
    with urllib.request.urlopen(req, context=ctx) as response:
        data = json.loads(response.read().decode('utf-8'))
        for r in data.get('results', []):
            print("Name:", r.get('display_name'))
            print("Homepage:", r.get('homepage_url'))
            print("IDS:", r.get('ids'))
except Exception as e:
    print("Error:", e)

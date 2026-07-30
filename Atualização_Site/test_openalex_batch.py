import urllib.request
import urllib.parse
import json
import ssl

# Bypass SSL verification
ctx = ssl._create_unverified_context()

# Test ISSNs
issns = ['2053-1583', '2190-572X', '2254-3376']
filter_str = '|'.join(issns)

params = {
    'filter': f'issn:{filter_str}',
    'select': 'issn,homepage_url,display_name',
    'per_page': 100,
    'mailto': 'jquad@example.com' # User email for polite pool
}

url = 'https://api.openalex.org/sources?' + urllib.parse.urlencode(params)
print("Requesting URL:", url)

req = urllib.request.Request(url, headers={'User-Agent': 'BuscadorPeriodicosAutobuild/1.0 (mailto:jquad@example.com)'})

try:
    with urllib.request.urlopen(req, context=ctx) as response:
        data = json.loads(response.read().decode('utf-8'))
        print("Success! Results found:", len(data.get('results', [])))
        for result in data.get('results', []):
            print(f"Name: {result.get('display_name')}")
            print(f"ISSNs: {result.get('issn')}")
            print(f"Homepage: {result.get('homepage_url')}")
            print("-" * 20)
except Exception as e:
    print("Error:", e)

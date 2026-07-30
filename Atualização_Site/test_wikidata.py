import urllib.request
import urllib.parse
import json
import ssl

ctx = ssl._create_unverified_context()

def get_wikidata_homepage(issn):
    sparql = f"""
    SELECT ?journal ?journalLabel ?website WHERE {{
      ?journal wdt:P236 "{issn}".
      ?journal wdt:P856 ?website.
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }}
    }}
    """
    
    url = 'https://query.wikidata.org/sparql?' + urllib.parse.urlencode({
        'query': sparql,
        'format': 'json'
    })
    
    req = urllib.request.Request(
        url,
        headers={
            'User-Agent': 'BuscadorPeriodicosAutobuild/1.0 (mailto:jquad@example.com)',
            'Accept': 'application/sparql-results+json'
        }
    )
    
    try:
        with urllib.request.urlopen(req, context=ctx) as response:
            data = json.loads(response.read().decode('utf-8'))
            bindings = data.get('results', {}).get('bindings', [])
            if bindings:
                return bindings[0].get('website', {}).get('value')
    except Exception as e:
        print(f"Error querying Wikidata for {issn}: {e}")
    return None

# Test with 2329-7662 (3D Printing and Additive Manufacturing)
# and another unresolved one like 0171-5410 (AAA - Arbeiten aus Anglistik und Amerikanistik)
test_issns = ['2329-7662', '0171-5410', '2564-7474']

for issn in test_issns:
    print(f"Querying Wikidata for ISSN {issn}...")
    site = get_wikidata_homepage(issn)
    print(f"Result: {site}")
    print("-" * 50)

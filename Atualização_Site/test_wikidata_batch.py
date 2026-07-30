import urllib.request
import urllib.parse
import json
import ssl

ctx = ssl._create_unverified_context()

def get_wikidata_homepages_batch(issns):
    values_str = ' '.join(f'"{issn}"' for issn in issns)
    sparql = f"""
    SELECT ?issn ?website WHERE {{
      VALUES ?issn {{ {values_str} }}
      ?journal wdt:P236 ?issn.
      ?journal wdt:P856 ?website.
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
    
    results = {}
    try:
        with urllib.request.urlopen(req, context=ctx) as response:
            data = json.loads(response.read().decode('utf-8'))
            bindings = data.get('results', {}).get('bindings', [])
            for bind in bindings:
                issn = bind.get('issn', {}).get('value')
                website = bind.get('website', {}).get('value')
                if issn and website:
                    results[issn] = website
    except Exception as e:
        print(f"Error querying Wikidata batch: {e}")
    return results

# Test batch
issns = ['2329-7662', '0171-5410', '2564-7474', '2053-1583']
res = get_wikidata_homepages_batch(issns)
print("Batch Results:")
print(res)

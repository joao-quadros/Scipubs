import json
import csv

# Load Wikidata cache
with open('wikidata_cache.json', 'r', encoding='utf-8') as f:
    cache = json.load(f)

# Find positive mappings
found = {k: v for k, v in cache.items() if v}
print(f"Total ISSNs mapped by Wikidata: {len(found)}")

# Read CSV and print some samples updated by Wikidata
samples = []
with open('dados.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f, delimiter=';')
    for row in reader:
        title = row.get('\ufeffTítulo da Revista') or row.get('Título da Revista') or row.get('Ttulo da Revista') or ''
        for k in row.keys():
            if 'Título' in k or 'Ttulo' in k or '\ufeffT' in k:
                title = row[k]
                break
        homepage = row.get('Homepage', '').strip()
        issn = row.get('ISSN', '').strip()
        
        if issn in found and homepage == found[issn]:
            samples.append((title, issn, homepage))
            if len(samples) >= 10:
                break

print("\n10 Samples Updated via Wikidata:")
print("=" * 80)
for title, issn, homepage in samples:
    print(f"Title: {title}")
    print(f"ISSN : {issn}")
    print(f"URL  : {homepage}")
    print("-" * 80)

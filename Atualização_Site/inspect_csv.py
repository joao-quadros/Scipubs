import csv
from collections import Counter

csv_path = 'dados.csv'
unique_issns = set()
unique_titles = set()
issn_to_rows = {}
indexers = Counter()

with open(csv_path, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f, delimiter=';')
    for row in reader:
        title = row.get('\ufeffTítulo da Revista') or row.get('Título da Revista') or row.get('Ttulo da Revista') or ''
        # Let's handle different possible encodings or keys
        for k in row.keys():
            if 'Título' in k or 'Ttulo' in k or '\ufeffT' in k:
                title = row[k]
                break
        issn = row.get('ISSN', '').strip()
        indexer = row.get('Indexador', '').strip()
        
        indexers[indexer] += 1
        if issn:
            unique_issns.add(issn)
            issn_to_rows.setdefault(issn, []).append(row)
        if title:
            unique_titles.add(title)

print(f"Unique ISSNs: {len(unique_issns)}")
print(f"Unique Titles: {len(unique_titles)}")
print("Indexers breakdown:", dict(indexers))

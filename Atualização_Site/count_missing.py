import csv

csv_path = 'dados.csv'
missing_issns = set()

with open(csv_path, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f, delimiter=';')
    for row in reader:
        homepage = row.get('Homepage', '').strip()
        issn = row.get('ISSN', '').strip()
        if not homepage and issn:
            missing_issns.add(issn)

print(f"Unique ISSNs still missing homepages: {len(missing_issns)}")

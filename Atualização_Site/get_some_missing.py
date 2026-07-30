import csv

csv_path = 'dados.csv'
missing = []

with open(csv_path, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f, delimiter=';')
    for row in reader:
        title = row.get('\ufeffTítulo da Revista') or row.get('Título da Revista') or row.get('Ttulo da Revista') or ''
        for k in row.keys():
            if 'Título' in k or 'Ttulo' in k or '\ufeffT' in k:
                title = row[k]
                break
        homepage = row.get('Homepage', '').strip()
        issn = row.get('ISSN', '').strip()
        if not homepage and issn:
            missing.append((title, issn))

print(f"Total missing: {len(missing)}")
print("First 20 missing:")
for i, (title, issn) in enumerate(missing[:20], 1):
    print(f"{i}. Title: {title} | ISSN: {issn}")

import csv

csv_path = 'dados.csv'
unresolved = []

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
            unresolved.append((title, issn))
            if len(unresolved) >= 10:
                break

print("10 Unresolved Journals:")
for title, issn in unresolved:
    print(f"Title: {title} | ISSN: {issn}")

import csv

csv_path = 'dados.csv'
updated_samples = []

with open(csv_path, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f, delimiter=';')
    
    # We want to find rows that have a Homepage populated.
    # We'll print some of them to inspect.
    for row in reader:
        title = row.get('\ufeffTítulo da Revista') or row.get('Título da Revista') or row.get('Ttulo da Revista') or ''
        for k in row.keys():
            if 'Título' in k or 'Ttulo' in k or '\ufeffT' in k:
                title = row[k]
                break
        homepage = row.get('Homepage', '').strip()
        issn = row.get('ISSN', '').strip()
        
        if homepage:
            updated_samples.append({
                'Title': title,
                'ISSN': issn,
                'Homepage': homepage
            })
            if len(updated_samples) >= 15:
                break

print("Verification Samples (15 Journals with updated homepages):")
print("=" * 80)
for sample in updated_samples:
    print(f"Title   : {sample['Title']}")
    print(f"ISSN    : {sample['ISSN']}")
    print(f"Homepage: {sample['Homepage']}")
    print("-" * 80)

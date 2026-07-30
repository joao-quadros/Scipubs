import csv

csv_path = 'dados.csv'
target_issns = {'0002-9726', '0002-9823', '0004-3400', '0004-4083', '0004-6574'}

print("Verifying updated rows in dados.csv:")
print("=" * 80)
with open(csv_path, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f, delimiter=';')
    for row in reader:
        issn = row.get('ISSN', '').strip()
        if issn in target_issns:
            # Find title key dynamically
            title = ''
            for k in row.keys():
                if 'título' in k.lower() or 'ttulo' in k.lower() or '\ufefft' in k.lower():
                    title = row[k]
                    break
            homepage = row.get('Homepage', '').strip()
            print(f"ISSN    : {issn}")
            print(f"Title   : {title}")
            print(f"Homepage: {homepage}")
            print("-" * 80)

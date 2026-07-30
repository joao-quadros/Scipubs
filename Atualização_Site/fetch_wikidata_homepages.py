import csv
import json
import os
import urllib.request
import urllib.parse
import ssl
import time

CSV_PATH = 'dados.csv'
CACHE_PATH = 'wikidata_cache.json'
BATCH_SIZE = 200
DELAY_SECS = 0.5

ssl_context = ssl._create_unverified_context()

def load_cache():
    if os.path.exists(CACHE_PATH):
        try:
            with open(CACHE_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load cache: {e}. Starting fresh.")
    return {}

def save_cache(cache):
    try:
        with open(CACHE_PATH, 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Warning: Failed to save cache: {e}")

def fetch_wikidata_batch(issns_batch):
    values_str = ' '.join(f'"{issn}"' for issn in issns_batch)
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
    
    mapped_results = {}
    try:
        with urllib.request.urlopen(req, context=ssl_context) as response:
            data = json.loads(response.read().decode('utf-8'))
            bindings = data.get('results', {}).get('bindings', [])
            for bind in bindings:
                issn = bind.get('issn', {}).get('value')
                website = bind.get('website', {}).get('value')
                if issn and website:
                    mapped_results[issn] = website
    except Exception as e:
        print(f"Error querying Wikidata batch: {e}")
    return mapped_results

def main():
    print("Loading data from dados.csv...")
    rows = []
    headers = []
    
    with open(CSV_PATH, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f, delimiter=';')
        headers = reader.fieldnames
        for row in reader:
            rows.append(row)
            
    print(f"Read {len(rows)} rows.")
    
    # Determine the actual header keys
    homepage_col = 'Homepage'
    issn_col = 'ISSN'
    for h in headers:
        if h.lower() == 'homepage':
            homepage_col = h
        elif h.lower() == 'issn':
            issn_col = h

    # Load cache
    cache = load_cache()
    print(f"Loaded Wikidata cache with {len(cache)} mapped ISSNs.")

    # Find unique ISSNs still missing homepage in CSV and not in cache
    missing_issns = set()
    for row in rows:
        homepage = row.get(homepage_col, '').strip()
        issn = row.get(issn_col, '').strip()
        if not homepage and issn:
            if issn not in cache:
                missing_issns.add(issn)

    missing_issns = list(missing_issns)
    total_to_fetch = len(missing_issns)
    print(f"Unique ISSNs missing homepages to fetch from Wikidata: {total_to_fetch}")

    if total_to_fetch > 0:
        print(f"Fetching in batches of {BATCH_SIZE}...")
        for idx in range(0, total_to_fetch, BATCH_SIZE):
            batch = missing_issns[idx:idx+BATCH_SIZE]
            print(f"Processing batch {idx // BATCH_SIZE + 1} / {(total_to_fetch - 1) // BATCH_SIZE + 1} ({len(batch)} ISSNs)...")
            
            # Fetch from Wikidata
            batch_results = fetch_wikidata_batch(batch)
            
            # Add to cache (mark not found as empty string so we don't query again)
            for issn in batch:
                cache[issn] = batch_results.get(issn, '')
                
            save_cache(cache)
            time.sleep(DELAY_SECS)

    print("\nUpdating dados.csv with homepages from Wikidata cache...")
    updated_count = 0
    not_found_count = 0
    
    # Apply cache to the rows
    for row in rows:
        homepage = row.get(homepage_col, '').strip()
        issn = row.get(issn_col, '').strip()
        if not homepage and issn:
            cached_val = cache.get(issn, '')
            if cached_val:
                row[homepage_col] = cached_val
                updated_count += 1
            else:
                not_found_count += 1

    # Save to CSV
    with open(CSV_PATH, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers, delimiter=';')
        writer.writeheader()
        writer.writerows(rows)

    print(f"Successfully updated CSV!")
    print(f"Rows updated with Wikidata links: {updated_count}")
    print(f"Rows still missing links: {not_found_count}")
    print("Done!")

if __name__ == '__main__':
    main()

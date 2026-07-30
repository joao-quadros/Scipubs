import csv
import json
import os
import urllib.request
import urllib.parse
import ssl
import time

CSV_PATH = 'dados.csv'
CACHE_PATH = 'homepage_cache.json'
BATCH_SIZE = 50
MAILTO = 'jquad@example.com'  # User contact for OpenAlex polite pool
DELAY_SECS = 0.15  # Sleep between API calls

# Bypass SSL verification for python's urllib
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

def fetch_batch_from_openalex(issns_batch):
    filter_str = '|'.join(issns_batch)
    params = {
        'filter': f'issn:{filter_str}',
        'select': 'issn,homepage_url',
        'per_page': 100,
        'mailto': MAILTO
    }
    url = 'https://api.openalex.org/sources?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(
        url, 
        headers={'User-Agent': f'BuscadorPeriodicosAutobuild/1.0 (mailto:{MAILTO})'}
    )
    
    mapped_homepages = {}
    try:
        with urllib.request.urlopen(req, context=ssl_context) as response:
            data = json.loads(response.read().decode('utf-8'))
            results = data.get('results', [])
            for result in results:
                homepage = result.get('homepage_url')
                if homepage:
                    # OpenAlex returns list of ISSNs for a source, map all of them
                    result_issns = result.get('issn', [])
                    for i in result_issns:
                        mapped_homepages[i] = homepage
    except Exception as e:
        print(f"Error fetching batch: {e}")
        # Return empty on failure so we can retry or skip
    return mapped_homepages

def main():
    print("Loading data from dados.csv...")
    rows = []
    headers = []
    
    # Read existing CSV file
    with open(CSV_PATH, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f, delimiter=';')
        headers = reader.fieldnames
        for row in reader:
            rows.append(row)
            
    print(f"Read {len(rows)} rows.")
    
    # Find column headers (handle BOM or variations)
    homepage_col = 'Homepage'
    issn_col = 'ISSN'
    
    # Determine the actual header keys
    for h in headers:
        if h.lower() == 'homepage':
            homepage_col = h
        elif h.lower() == 'issn':
            issn_col = h

    # Load previously fetched cache
    cache = load_cache()
    print(f"Loaded cache with {len(cache)} mapped ISSNs.")

    # Find unique ISSNs that have empty Homepage in CSV and are not in cache
    missing_issns = set()
    for row in rows:
        homepage = row.get(homepage_col, '').strip()
        issn = row.get(issn_col, '').strip()
        if not homepage and issn:
            if issn not in cache:
                missing_issns.add(issn)

    missing_issns = list(missing_issns)
    total_to_fetch = len(missing_issns)
    print(f"Unique ISSNs missing homepages to fetch: {total_to_fetch}")

    if total_to_fetch > 0:
        print(f"Fetching in batches of {BATCH_SIZE}...")
        for idx in range(0, total_to_fetch, BATCH_SIZE):
            batch = missing_issns[idx:idx+BATCH_SIZE]
            print(f"Processing batch {idx // BATCH_SIZE + 1} / {(total_to_fetch - 1) // BATCH_SIZE + 1} ({len(batch)} ISSNs)...")
            
            # Fetch from OpenAlex
            batch_results = fetch_batch_from_openalex(batch)
            
            # Add results to cache
            # Note: even if an ISSN is not found or has no homepage, we mark it in cache as None/empty
            # so we don't query it again on resume.
            for issn in batch:
                cache[issn] = batch_results.get(issn, '')
            
            # Save cache every batch
            save_cache(cache)
            time.sleep(DELAY_SECS)
            
    print("\nUpdating dados.csv with homepages from cache...")
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

    # Write updated rows back to CSV
    with open(CSV_PATH, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers, delimiter=';')
        writer.writeheader()
        writer.writerows(rows)

    print(f"Successfully updated CSV!")
    print(f"Rows updated with new links: {updated_count}")
    print(f"Rows still missing links (not found/empty): {not_found_count}")
    print("Done!")

if __name__ == '__main__':
    main()

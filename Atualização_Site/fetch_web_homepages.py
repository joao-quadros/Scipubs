import csv
import json
import os
import sys
import urllib.request
import urllib.parse
import ssl
import time
import random
import shutil
import re
from bs4 import BeautifulSoup

# Paths
CSV_PATH = 'dados.csv'
BACKUP_PATH = 'dados_backup.csv'
CACHE_PATH = 'web_cache.json'

# SSL context to bypass verification if needed
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

def fetch_ddg_lite_raw(title, issn):
    # Formulate query
    query = f"{title} journal ISSN {issn} official website"
    url = 'https://lite.duckduckgo.com/lite/'
    data = urllib.parse.urlencode({'q': query}).encode('utf-8')
    
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
    )
    
    try:
        with urllib.request.urlopen(req, context=ssl_context, timeout=10) as response:
            html = response.read().decode('utf-8')
            
            # Check for bot challenge
            if any(x in html.lower() for x in ["captcha", "robot", "human", "unusual traffic"]):
                return "BLOCKED", None
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find result links
            links = []
            for a in soup.find_all('a', class_='result-link'):
                href = a.get('href')
                if href and href.startswith('http'):
                    links.append(href)
            
            # Fallback to any external links starting with http if class result-link is empty
            if not links:
                for a in soup.find_all('a'):
                    href = a.get('href')
                    if href and href.startswith('http') and not any(d in href for d in ['duckduckgo.com', '/']):
                        links.append(href)
            
            return "SUCCESS", links
    except Exception as e:
        return f"ERROR: {e}", None

def fetch_yahoo_raw(title, issn):
    # Formulate query
    query = f"{title} journal ISSN {issn} official website"
    params = urllib.parse.urlencode({'p': query})
    url = f'https://search.yahoo.com/search?{params}'
    
    req = urllib.request.Request(
        url,
        headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
        }
    )
    
    try:
        with urllib.request.urlopen(req, context=ssl_context, timeout=10) as response:
            html = response.read().decode('utf-8')
            
            # Check for bot challenge
            if any(x in html.lower() for x in ["captcha", "robot", "unusual activity"]):
                return "BLOCKED", None
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Yahoo search results are redirected through r.search.yahoo.com
            links = []
            for a in soup.find_all('a'):
                href = a.get('href')
                if href and 'r.search.yahoo.com' in href:
                    m = re.search(r'/RU=(.+?)/RK=', href)
                    if m:
                        decoded = urllib.parse.unquote(m.group(1))
                        links.append(decoded)
            
            return "SUCCESS", links
    except Exception as e:
        return f"ERROR: {e}", None

def search_ddg_lite(title, issn):
    blocklist = [
        'duckduckgo',
        'portal.issn.org',
        'wikipedia',
        'wikidata',
        'facebook',
        'twitter',
        'linkedin',
        'youtube',
        'instagram',
        'researchgate',
        'academia.edu',
        'scopus',
        'webofscience',
        'crossref',
        'openalex',
        'google',
        'yahoo',
        'yimg',
        'bing',
        'uservoice'
    ]
    
    # 1. Try DuckDuckGo Lite
    status, links = fetch_ddg_lite_raw(title, issn)
    
    # 2. Fall back to Yahoo Search if DuckDuckGo Lite is blocked or fails
    if status != "SUCCESS" or not links:
        if status == "BLOCKED":
            print("  [DDG blocked by CAPTCHA, falling back to Yahoo Search...]")
        else:
            print(f"  [DDG search status: {status}, trying Yahoo Search...]")
            
        status, links = fetch_yahoo_raw(title, issn)
        if status != "SUCCESS":
            print(f"  [Yahoo search status: {status}]")
            return None
            
    if not links:
        return None
        
    # Filter links by blocklist
    filtered_links = []
    for link in links:
        is_blocked = False
        for domain in blocklist:
            if domain in link.lower():
                is_blocked = True
                break
        if not is_blocked:
            filtered_links.append(link)
            
    if filtered_links:
        return filtered_links[0]
    return None

def main():
    # Try to reconfigure stdout to handle unicode correctly on Windows consoles
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except AttributeError:
        pass

    # 1. Parse Arguments (optional limit)
    limit = None
    if '--limit' in sys.argv:
        try:
            limit_idx = sys.argv.index('--limit') + 1
            limit = int(sys.argv[limit_idx])
            print(f"Running in verification mode. Limit: {limit} queries.")
        except Exception as e:
            print(f"Error parsing limit: {e}")
            sys.exit(1)

    # 2. Backup Step
    if not os.path.exists(CSV_PATH):
        print(f"Error: Database file '{CSV_PATH}' not found!")
        sys.exit(1)
        
    print(f"Creating backup: '{CSV_PATH}' -> '{BACKUP_PATH}'...")
    try:
        shutil.copy2(CSV_PATH, BACKUP_PATH)
        print("Backup verified successfully.")
    except Exception as e:
        print(f"Error creating backup: {e}")
        sys.exit(1)

    # 3. Read Database
    print("Reading database...")
    rows = []
    headers = []
    with open(CSV_PATH, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f, delimiter=';')
        headers = reader.fieldnames
        for row in reader:
            rows.append(row)
    print(f"Loaded {len(rows)} rows from database.")

    # Identify correct column headers
    homepage_col = 'Homepage'
    issn_col = 'ISSN'
    title_col = None
    
    for h in headers:
        if h.lower() == 'homepage':
            homepage_col = h
        elif h.lower() == 'issn':
            issn_col = h
        elif any(x in h.lower() for x in ['título', 'ttulo', '\ufefft']):
            title_col = h

    if not title_col:
        # Fallback if no matching title column was found
        title_col = headers[0]
    
    # Strip any BOM character from printed column names to avoid UnicodeEncodeErrors
    issn_col_print = issn_col.replace('\ufeff', '')
    title_col_print = title_col.replace('\ufeff', '')
    homepage_col_print = homepage_col.replace('\ufeff', '')
    print(f"Using column names: ISSN='{issn_col_print}', Title='{title_col_print}', Homepage='{homepage_col_print}'")

    # Load cache
    cache = load_cache()
    print(f"Loaded cache with {len(cache)} mapped ISSNs.")

    # Identify ISSNs to fetch
    issn_to_title = {}
    missing_issns = set()
    
    for row in rows:
        homepage = row.get(homepage_col, '').strip()
        issn = row.get(issn_col, '').strip()
        if issn:
            title = row.get(title_col, '').strip()
            if issn not in issn_to_title or len(title) > len(issn_to_title[issn]):
                issn_to_title[issn] = title
            if not homepage:
                missing_issns.add(issn)

    print(f"Total unique ISSNs in dataset missing homepages: {len(missing_issns)}")
    
    # Exclude already cached ones
    to_fetch = [issn for issn in sorted(list(missing_issns)) if issn not in cache]
    print(f"Unique ISSNs to query in this run: {len(to_fetch)}")

    if limit is not None:
        to_fetch = to_fetch[:limit]
        print(f"Limiting to first {len(to_fetch)} queries.")

    # 4. Search Loop
    count = 0
    found_count = 0
    
    for issn in to_fetch:
        title = issn_to_title.get(issn, '')
        count += 1
        print(f"[{count}/{len(to_fetch)}] Searching: ISSN {issn} | Title: {title}...")
        
        homepage = search_ddg_lite(title, issn)
        
        # Cache results (empty string if not found, to mark as processed)
        cache[issn] = homepage or ''
        save_cache(cache)
        
        if homepage:
            found_count += 1
            print(f"  --> FOUND: {homepage}")
        else:
            print("  --> NOT FOUND")
            
        # Jitter delay: 1.5s - 2.5s
        delay = 1.5 + random.random() * 1.0
        time.sleep(delay)

    # 5. Merge and Save back to CSV
    print("\nMerging results back into database...")
    updated_rows = 0
    for row in rows:
        homepage = row.get(homepage_col, '').strip()
        issn = row.get(issn_col, '').strip()
        if not homepage and issn:
            cached_val = cache.get(issn, '')
            if cached_val:
                row[homepage_col] = cached_val
                updated_rows += 1

    # Save to CSV
    print(f"Saving updated database to '{CSV_PATH}'...")
    with open(CSV_PATH, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers, delimiter=';')
        writer.writeheader()
        writer.writerows(rows)

    print("\nSummary:")
    print(f"  Backup created at: {BACKUP_PATH}")
    print(f"  Queries performed: {len(to_fetch)}")
    print(f"  Homepages found in this run: {found_count}")
    print(f"  Rows updated in CSV: {updated_rows}")
    print("Done!")

if __name__ == '__main__':
    main()

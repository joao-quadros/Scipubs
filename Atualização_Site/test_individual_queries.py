import urllib.request
import urllib.parse
import ssl

ctx = ssl._create_unverified_context()

def test_query(title, issn):
    query = f"{title} journal ISSN {issn} official website"
    print(f"Querying: {query}")
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
        with urllib.request.urlopen(req, context=ctx) as response:
            html = response.read().decode('utf-8')
            print("HTML Length:", len(html))
            print("HTML snippet:")
            print(html[:1000])
            if "captcha" in html.lower() or "robot" in html.lower() or "human" in html.lower():
                print("--- CAPTCHA/BOT DETECTION DETECTED ---")
            if "no results" in html.lower() or "didn't find" in html.lower() or "não foram encontrados" in html.lower():
                print("--- NO RESULTS FOUND MESSAGE IN HTML ---")
    except Exception as e:
        print("Error:", e)

test_query("ACM Transactions on Computing Education", "1946-6226")

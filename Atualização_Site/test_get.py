import urllib.request
import urllib.parse
import ssl

ctx = ssl._create_unverified_context()

def test_get():
    query = 'ACM Transactions on Computing Education journal ISSN 1946-6226 official website'
    params = urllib.parse.urlencode({'q': query})
    url = f'https://lite.duckduckgo.com/lite/?{params}'
    print(f"Querying GET: {url}")
    
    req = urllib.request.Request(
        url,
        headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5'
        }
    )
    try:
        with urllib.request.urlopen(req, context=ctx) as response:
            html = response.read().decode('utf-8')
            print("HTML Length:", len(html))
            if "captcha" in html.lower() or "robot" in html.lower() or "human" in html.lower() or "unusual traffic" in html.lower():
                print("--- BOT DETECTION DETECTED ---")
                with open("ddg_get_blocked.html", "w", encoding="utf-8") as f:
                    f.write(html)
            else:
                print("--- SUCCESS ---")
                with open("ddg_get_success.html", "w", encoding="utf-8") as f:
                    f.write(html)
    except Exception as e:
        print("Error:", e)

if __name__ == '__main__':
    test_get()

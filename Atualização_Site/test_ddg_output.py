import urllib.request
import urllib.parse
import ssl

ctx = ssl._create_unverified_context()

def test():
    query = '3D Printing and Additive Manufacturing journal ISSN 2329-7662 official website'
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
    with urllib.request.urlopen(req, context=ctx) as response:
        html = response.read().decode('utf-8')
        print("HTML length:", len(html))
        with open("ddg_raw.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("Saved raw HTML to ddg_raw.html")

if __name__ == '__main__':
    test()

from bs4 import BeautifulSoup

with open("ddg_get_blocked.html", "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, "html.parser")
print("Page Title:", soup.title.string if soup.title else "No Title")
print("Text Content:")
print(soup.get_text(separator="\n", strip=True)[:1000])

from bs4 import BeautifulSoup
import re

with open("ddg_raw.html", "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, "html.parser")

# Let's find all links and inspect what is in them
print("ALL HREFS:")
for a in soup.find_all("a"):
    href = a.get("href")
    text = a.get_text(strip=True)
    if href:
        print(f"Text: {text[:40]} | Href: {href[:80]}")

print("\n--- DETAILED LOOK AT RESULT LINKS ---")
# On DDG Lite, results are usually inside tables.
# Let's inspect rows with class result-link or td elements
for row in soup.find_all(class_=re.compile("result")):
    print(row.name, row.get("class"), row.get_text(strip=True)[:100])

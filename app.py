# app.py
import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify, request

app = Flask(__name__)

LISTING_URL = "https://www.saps.gov.za/newsroom/ms.php"
DETAIL_BASE = "https://www.saps.gov.za/newsroom/msspeechdetail.php?nid="

def truncate(text: str, max_chars: int) -> str:
    return text if len(text) <= max_chars else text[:max_chars] + "…"

@app.route("/latest", methods=["GET"])
def latest():
    """
    Returns recent SAPS press releases.
    Query params:
      - limit: how many items to return (default 3)
      - max_chars: trim each body to this many characters (default 6000)
    """
    # 1) read query params with safe defaults
    try:
        limit = int(request.args.get("limit", 3))
    except ValueError:
        limit = 3
    try:
        max_chars = int(request.args.get("max_chars", 6000))
    except ValueError:
        max_chars = 6000

    headers = {"User-Agent": "Mozilla/5.0"}
    # 2) fetch listing
    r = requests.get(LISTING_URL, headers=headers, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    out = []
    # 3) take only 'limit' items from the listing
    for a in soup.select("a[href*='msspeechdetail.php?nid=']")[:limit]:
        href = a.get("href", "")
        if "nid=" not in href:
            continue
        nid = href.split("nid=")[-1]
        title = a.get_text(strip=True)

        # 4) fetch detail page
        d = requests.get(DETAIL_BASE + nid, headers=headers, timeout=20)
        d.raise_for_status()
        dsoup = BeautifulSoup(d.text, "html.parser")
        # main content paragraphs (fallbacks omitted for simplicity)
        body = " ".join(
            p.get_text(" ", strip=True)
            for p in dsoup.select("div.newscontent p")
        )
        body = truncate(body, max_chars)

        out.append({"nid": nid, "title": title, "body": body})

    return jsonify(out)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)

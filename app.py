# app.py — SAPS fetcher (robust selectors + trimming + debug)
from flask import Flask, jsonify, request
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

LISTING_URL = "https://www.saps.gov.za/newsroom/ms.php"
DETAIL_BASE = "https://www.saps.gov.za/newsroom/msspeechdetail.php?nid="

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/127.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-ZA,en;q=0.9",
    "Connection": "close",
}

def truncate(text: str, max_chars: int) -> str:
    return text if len(text) <= max_chars else text[:max_chars] + "…"

def extract_body(html: str) -> str:
    """Try multiple containers; fall back to full page text."""
    soup = BeautifulSoup(html, "html.parser")
    for sel in [
        "div.newscontent p",
        "div#content p",
        "article p",
        "div.content p",
        "main p",
        "p",
    ]:
        ps = [p.get_text(" ", strip=True) for p in soup.select(sel)]
        ps = [p for p in ps if p and len(p) > 25]
        if ps:
            return "\n".join(ps).strip()
    return soup.get_text(" ", strip=True)

@app.get("/latest")
def latest():
    """
    Return recent SAPS releases with trimmed bodies.

    Query params:
      - limit: number of items to return (default 3)
      - max_chars: trim each body (default 6000)
      - debug: 1 to include minimal debug info
    """
    try:
        limit = int(request.args.get("limit", 3))
    except ValueError:
        limit = 3
    try:
        max_chars = int(request.args.get("max_chars", 6000))
    except ValueError:
        max_chars = 6000
    debug = request.args.get("debug", "0") == "1"

    # 1) Fetch listing
    lr = requests.get(LISTING_URL, headers=HEADERS, timeout=25)
    status_listing = lr.status_code
    lr.raise_for_status()
    lsoup = BeautifulSoup(lr.text, "html.parser")

    items = []
    # ✅ Correct selector for SAPS newsroom links:
    links = lsoup.select("a[href*='msspeechdetail.php?nid=']")
    for a in links[:limit]:
        href = a.get("href") or ""
        if "nid=" not in href:
            continue
        nid = href.split("nid=")[-1].strip()
        title = a.get_text(strip=True) or f"SAPS release {nid}"

        detail_url = DETAIL_BASE + nid

        # 2) Fetch detail page
        dr = requests.get(detail_url, headers=HEADERS, timeout=25, allow_redirects=True)
        status_detail = dr.status_code
        body = extract_body(dr.text).strip()
        body = truncate(body, max_chars)

        item = {
            "nid": nid,
            "title": title,
            "body": body,
            "url": detail_url,
        }
        if debug:
            item["status_detail"] = status_detail
            if not body:
                item["detail_snippet"] = truncate(dr.text, 400)

        items.append(item)

    return jsonify({"status_listing": status_listing, "count": len(items), "items": items})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)

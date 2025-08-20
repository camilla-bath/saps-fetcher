# app.py (robust fetcher with debugging)
import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify, request

app = Flask(__name__)

LISTING_URL = "https://www.saps.gov.za/newsroom/ms.php"
DETAIL_BASE = "https://www.saps.gov.za/newsroom/msspeechdetail.php?nid="

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-ZA,en;q=0.9",
    "Connection": "close",
}

def truncate(text: str, max_chars: int) -> str:
    return text if len(text) <= max_chars else text[:max_chars] + "…"

def extract_body(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    # try several likely containers/selectors
    for sel in [
        "div.newscontent p",
        "div#content p",
        "article p",
        "div.content p",
        "main p",
        "p",
    ]:
        parts = [p.get_text(" ", strip=True) for p in soup.select(sel)]
        parts = [p for p in parts if p and len(p) > 25]
        if parts:
            return "\n".join(parts).strip()
    # fallback: whole page text (last resort)
    return soup.get_text(" ", strip=True)

@app.route("/latest", methods=["GET"])
def latest():
    """Return recent SAPS releases with trimmed bodies.
       Query params: limit (default 3), max_chars (default 6000), debug (0/1)
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

    # fetch listing
    lr = requests.get(LISTING_URL, headers=HEADERS, timeout=25)
    status_listing = lr.status_code
    lr.raise_for_status()
    lsoup = BeautifulSoup(lr.text, "html.parser")

    results = []
    for a in lsoup.select("a[href*='msspeechdetail.php?nid=']")[:limit]:
        href = a.get("href") or ""
        if "nid=" not in href:
            continue
        nid = href.split("nid=")[-1].strip()
        title = a.get_text(strip=True)

        detail_url = DETAIL_BASE + nid
        dr = requests.get(detail_url, headers=HEADERS, timeout=25, allow_redirects=True)
        status_detail = dr.status_code
        body = extract_body(dr.text).strip()
        body = truncate(body, max_chars)

        item = {
            "nid": nid,
            "title": title,
            "body": body if body else "",
        }

        if debug:
            # include minimal debug so we can see if we’re blocked
            item["detail_url"] = detail_url
            item["st]()

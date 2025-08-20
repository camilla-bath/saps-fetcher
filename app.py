from flask import Flask, jsonify, request
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

LISTING_URL = "https://www.saps.gov.za/newsroom/ms.php"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/127.0.0.0 Safari/537.36"
}


@app.route("/latest", methods=["GET"])
def get_latest():
    limit = int(request.args.get("limit", 3))
    max_chars = int(request.args.get("max_chars", 6000))

    # Fetch listing page
    lr = requests.get(LISTING_URL, headers=HEADERS, timeout=25, allow_redirects=True)
    if lr.status_code != 200:
        return jsonify({"error": "Failed to fetch SAPS newsroom"}), 500

    soup = BeautifulSoup(lr.text, "html.parser")
    links = soup.select("a.newsroom")  # SAPS newsroom links
    results = []

    for link in links[:limit]:
        detail_url = "https://www.saps.gov.za/newsroom/" + link.get("href")

        # ✅ FIXED: closed properly with timeout + allow_redirects
        dr = requests.get(detail_url, headers=HEADERS, timeout=25, allow_redirects=True)
        if dr.status_code != 200:
            continue

        detail_soup = BeautifulSoup(dr.text, "html.parser")
        title = detail_soup.find("h1").get_text(strip=True) if detail_soup.find("h1") else "No Title"
        body = " ".join(p.get_text(strip=True) for p in detail_soup.find_all("p"))

        # Trim if too long
        if len(body) > max_chars:
            body = body[:max_chars] + "..."

        results.append({"title": title, "body": body, "url": detail_url})

    return jsonify(results)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

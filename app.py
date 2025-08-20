# saps_fetcher.py
import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify

app = Flask(__name__)

LISTING_URL = "https://www.saps.gov.za/newsroom/ms.php"
DETAIL_BASE = "https://www.saps.gov.za/newsroom/msspeechdetail.php?nid="

@app.route("/latest", methods=["GET"])
def latest():
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(LISTING_URL, headers=headers, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    out = []
    for a in soup.select("a[href*='msspeechdetail.php?nid=']")[:5]:  # grab 5 latest
        nid = a.get("href").split("nid=")[-1]
        title = a.get_text(strip=True)
        detail = requests.get(DETAIL_BASE + nid, headers=headers, timeout=20)
        dsoup = BeautifulSoup(detail.text, "html.parser")
        body = " ".join(p.get_text(" ", strip=True) for p in dsoup.select("div.newscontent p"))
        out.append({"nid": nid, "title": title, "body": body})
    return jsonify(out)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)

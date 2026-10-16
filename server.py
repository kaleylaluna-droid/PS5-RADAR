from flask import Flask, jsonify, send_from_directory
import requests, re, html, os, time
from bs4 import BeautifulSoup
from datetime import datetime, timezone

app = Flask(__name__, static_folder=".", static_url_path="")
HEADERS = {
    "User-Agent": "PS5RadarPersonal/1.0 (personal videogame tracking app; contact: local user)",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.7",
}
CACHE = {}
CACHE_SECONDS = 30 * 60

SOURCES = {
    "releases": "https://vandal.elespanol.com/lanzamientos/89/playstation-5",
    "reviews": "https://vandal.elespanol.com/analisis/playstation-5",
    "offers": "https://store.playstation.com/es-es/category/c48c22e2-5f2e-40e4-b946-8fdb97a0bc32/1",
}

def fetch_text(url):
    r = requests.get(url, headers=HEADERS, timeout=18)
    r.raise_for_status()
    r.encoding = r.apparent_encoding or "utf-8"
    return r.text

def clean(s):
    return re.sub(r"\s+", " ", html.unescape(s or "")).strip()

def cached(key, producer):
    now = time.time()
    if key in CACHE and now - CACHE[key][0] < CACHE_SECONDS:
        return CACHE[key][1]
    value = producer()
    CACHE[key] = (now, value)
    return value

def scrape_vandal_releases():
    url = SOURCES["releases"]
    soup = BeautifulSoup(fetch_text(url), "html.parser")
    items, seen = [], set()
    # The Vandal release page contains dated rows and links to individual game pages.
    for a in soup.select("a[href]"):
        title = clean(a.get_text(" ", strip=True))
        href = a.get("href", "")
        if not title or len(title) < 3 or not href.startswith("http") or "vandal.elespanol.com" not in href:
            continue
        parent = a.parent
        context = clean(parent.get_text(" ", strip=True)) if parent else title
        if not re.search(r"\b(?:20\d{2}|por confirmar|sin fecha|octubre|noviembre|diciembre|enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre)\b", context, re.I):
            continue
        if not re.search(r"\bPS5\b|PlayStation 5|playstation-5|/juegos/", href + " " + context, re.I):
            # Release page itself already filters PS5; keep date rows from that page.
            if not re.search(r"\d{1,2}/\d{1,2}/20\d{2}", context):
                continue
        date_match = re.search(r"\b(\d{1,2}/\d{1,2}/20\d{2}|(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s+20\d{2}|20\d{2}|Por confirmar)\b", context, re.I)
        date = date_match.group(1) if date_match else ""
        key = (title.lower(), href)
        if key in seen or title.lower() in {"seguir", "comprar en game", "ps5", "lanzamientos"}:
            continue
        seen.add(key)
        items.append({"title": title, "date": date, "summary": context[:260], "source": "Vandal", "url": href})
        if len(items) >= 80:
            break
    return {"items": items, "source_url": url, "updated_at": datetime.now(timezone.utc).isoformat()}

def scrape_vandal_reviews():
    url = SOURCES["reviews"]
    soup = BeautifulSoup(fetch_text(url), "html.parser")
    items, seen = [], set()
    for a in soup.select("a[href]"):
        title = clean(a.get_text(" ", strip=True))
        href = a.get("href", "")
        if not title or len(title) < 5 or "vandal.elespanol.com" not in href:
            continue
        context = clean(a.parent.get_text(" ", strip=True)) if a.parent else title
        if not re.search(r"análisis|analisis|review", (title + " " + context), re.I):
            continue
        if href in seen:
            continue
        seen.add(href)
        score = ""
        m = re.search(r"\b(?:nota|puntuación)\s*:?\s*(10|[0-9])(?:[.,]\d+)?\b", context, re.I)
        if m: score = m.group(1)
        items.append({"title": title, "summary": context[:260], "score": score, "source": "Vandal", "url": href})
        if len(items) >= 60: break
    return {"items": items, "source_url": url, "updated_at": datetime.now(timezone.utc).isoformat()}

def scrape_ps_store_offers():
    url = SOURCES["offers"]
    soup = BeautifulSoup(fetch_text(url), "html.parser")
    # Storefront markup changes frequently; parse visible product cards and links.
    items, seen = [], set()
    for a in soup.select('a[href*="/product/"]'):
        href = a.get("href", "")
        title = clean(a.get_text(" ", strip=True))
        if not title or len(title) < 2:
            continue
        parent = a
        for _ in range(4):
            if parent.parent: parent = parent.parent
        context = clean(parent.get_text(" ", strip=True))
        if "PS5" not in context.upper() and "PS5" not in title.upper():
            continue
        price_match = re.search(r"(\d{1,3}[,.]\d{2})\s*€", context)
        original_match = re.search(r"(?:Precio original|antes)\s*:?\s*(\d{1,3}[,.]\d{2})\s*€", context, re.I)
        discount_match = re.search(r"(-\d{1,2}\s*%|Ahorra un \d{1,2}\s*%)", context, re.I)
        if not discount_match and not original_match:
            continue
        key = (title.lower(), href)
        if key in seen: continue
        seen.add(key)
        full_url = href if href.startswith("http") else "https://store.playstation.com" + href
        items.append({
            "title": title, "summary": context[:250],
            "price": (price_match.group(1) + " €") if price_match else "",
            "discount": discount_match.group(1) if discount_match else "",
            "source": "PlayStation Store España", "url": full_url
        })
        if len(items) >= 100: break
    return {"items": items, "source_url": url, "updated_at": datetime.now(timezone.utc).isoformat()}

@app.get("/")
def home():
    return send_from_directory(".", "index.html")

@app.get("/api/health")
def health():
    return jsonify({"ok": True, "service": "PS5 Radar", "sources": SOURCES, "checked_at": datetime.now(timezone.utc).isoformat()})

@app.get("/api/releases")
def releases():
    try:
        return jsonify(cached("releases", scrape_vandal_releases))
    except Exception as e:
        return jsonify({"items": [], "error": str(e), "source_url": SOURCES["releases"]}), 502

@app.get("/api/reviews")
def reviews():
    try:
        return jsonify(cached("reviews", scrape_vandal_reviews))
    except Exception as e:
        return jsonify({"items": [], "error": str(e), "source_url": SOURCES["reviews"]}), 502

@app.get("/api/offers")
def offers():
    try:
        return jsonify(cached("offers", scrape_ps_store_offers))
    except Exception as e:
        return jsonify({"items": [], "error": str(e), "source_url": SOURCES["offers"]}), 502

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    app.run(host="0.0.0.0", port=port, debug=False)

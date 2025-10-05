import os
import time
import threading
from datetime import datetime
from flask import Flask, jsonify
import requests
from bs4 import BeautifulSoup
from twilio.rest import Client

app = Flask(__name__)

# ENV VARS
TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM = os.getenv("TWILIO_FROM")
PHONE_TO = os.getenv("PHONE_TO")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "120"))
USER_AGENT = os.getenv("USER_AGENT", "Mozilla/5.0 (compatible; PokemonBot/1.0)")

KEYWORDS = ["mega evolution", "phantasmal flames"]

RETAILERS = [
    {"name": "Walmart", "url": "https://www.walmart.com/search/?query={query}", "selector": "div[data-item-id]"},
    {"name": "Target", "url": "https://www.target.com/s?searchTerm={query}", "selector": "li.h-padding-a-none"},
    {"name": "GameStop", "url": "https://www.gamestop.com/search/?q={query}", "selector": "div.product-tile"},
    {"name": "BestBuy", "url": "https://www.bestbuy.com/site/searchpage.jsp?st={query}", "selector": "li.sku-item"},
    {"name": "Walgreens", "url": "https://www.walgreens.com/search/results.jsp?Ntt={query}", "selector": "div.product-info"},
    {"name": "Dollar General", "url": "https://www.dollargeneral.com/search?query={query}", "selector": "div.search-result-item"},
    {"name": "Pokémon Center", "url": "https://www.pokemoncenter.com/search?q={query}", "selector": "div.product-tile"}
]

client = Client(TWILIO_SID, TWILIO_TOKEN)
seen_hits = set()

def send_sms(msg):
    try:
        client.messages.create(body=msg, from_=TWILIO_FROM, to=PHONE_TO)
        print(f"[SMS SENT] {msg}")
    except Exception as e:
        print(f"SMS send error: {e}")

def check_site(retailer):
    hits = []
    for term in KEYWORDS:
        url = retailer["url"].format(query=requests.utils.quote(term))
        try:
            r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=15)
            soup = BeautifulSoup(r.text, "html.parser")
            for item in soup.select(retailer["selector"]):
                text = item.get_text(" ", strip=True).lower()
                if term in text and not any(x in text for x in ["out of stock", "sold out", "unavailable"]):
                    link_tag = item.find("a", href=True)
                    if link_tag:
                        link = link_tag['href']
                        if link.startswith("/"):
                            base = f"https://{retailer['name'].lower().replace(' ', '')}.com"
                            link = base + link
                    else:
                        link = url
                    hit_id = f"{retailer['name']}|{term}|{hash(text)}"
                    if hit_id not in seen_hits:
                        seen_hits.add(hit_id)
                        hits.append({"retailer": retailer["name"], "term": term, "link": link})
        except Exception as e:
            print(f"Error checking {retailer['name']}: {e}")
    return hits

def run_loop():
    while True:
        print(f"\n[CHECK] {datetime.utcnow().isoformat()} UTC")
        for r in RETAILERS:
            results = check_site(r)
            for result in results:
                # Single-line f-string to avoid errors
                msg = f"🔥 {result['term'].title()} in stock at {result['retailer']}! {result['link']}"
                send_sms(msg)
            time.sleep(3)
        time.sleep(CHECK_INTERVAL)

@app.before_first_request
def start_background():
    t = threading.Thread(target=run_loop, daemon=True)
    t.start()

@app.route("/")
def index():
    return "Pokémon Stock Notifier Running."

@app.route("/health")
def health():
    return jsonify({"status": "ok", "alerts": len(seen_hits)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))

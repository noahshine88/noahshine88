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

KEYWORDS = ["mega evolution", "phantasmal flames", "pokémon"]

RETAILERS = [
    {"name": "Walmart", "url": "https://www.walmart.com/search/?query={query}", "selector": "div[data-item-id]"},
    {"name": "Target", "url": "https://www.target.com/s?searchTerm={query}", "selector": "li.h-padding-a-none"},
    {"name": "GameStop", "url": "https://www.gamestop.com/search/?q={query}", "selector": "div.product-tile"},
    {"name": "BestBuy", "url": "https://www.bestbuy.com/site/searchpage.jsp?st={query}", "selector": "li.sku-item"},
    {"name": "Walgreens", "url": "https://www.walgreens.com/search/results.jsp?Ntt={query}", "selector": "div.product-info"},
    {"name": "Dollar General", "url": "https://www.dollargeneral.com/search?query={query}", "selector": "div.search-result-item"},
    {"name": "Pokémon Center", "url": "https://www.pokemoncenter.com/search?q={query}", "selector": "div.product-tile"}
]

client = Client(TWILIO

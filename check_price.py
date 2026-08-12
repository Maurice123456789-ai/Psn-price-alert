#!/usr/bin/env python3
"""
Kinguin PSN EUR 100 NL price checker for GitHub Actions
Sends Telegram alert when price <= 87 EUR
"""

import os
import re
import sys
import requests

try:
    import cloudscraper
    HAS_CLOUDSCRAPER = True
except ImportError:
    HAS_CLOUDSCRAPER = False

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "6571415052")
PRODUCT_URL = "https://www.kinguin.net/category/95893/playstation-network-eur-100-gift-card-nl"
TARGET_PRICE = 87.0

def send_telegram(message: str) -> bool:
    if not BOT_TOKEN:
        print("ERROR: TELEGRAM_BOT_TOKEN not set")
        return False
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }
    try:
        r = requests.post(url, data=payload, timeout=20)
        print(f"Telegram response: {r.status_code}")
        return r.json().get("ok", False)
    except Exception as e:
        print(f"Telegram error: {e}")
        return False

def get_price():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "nl-NL,nl;q=0.9,en;q=0.8",
    }

    html = None
    if HAS_CLOUDSCRAPER:
        try:
            scraper = cloudscraper.create_scraper()
            resp = scraper.get(PRODUCT_URL, timeout=40)
            if resp.status_code == 200:
                html = resp.text
                print("Fetched with cloudscraper")
        except Exception as e:
            print(f"cloudscraper failed: {e}")

    if not html:
        try:
            resp = requests.get(PRODUCT_URL, headers=headers, timeout=40)
            print(f"requests status: {resp.status_code}")
            if resp.status_code == 200:
                html = resp.text
        except Exception as e:
            print(f"requests failed: {e}")

    if not html:
        return None

    # Extract prices
    prices = []
    # Look for patterns like €87.50, 87,50 €, $95.00 etc.
    patterns = [
        r"[€$]\s*(\d+[.,]\d{2})",
        r"(\d+[.,]\d{2})\s*[€$]",
        r"(\d+[.,]\d{2})\s*EUR",
    ]
    for pat in patterns:
        for match in re.findall(pat, html, re.IGNORECASE):
            try:
                val = float(match.replace(",", "."))
                if 60.0 <= val <= 140.0:  # realistic range
                    prices.append(val)
            except ValueError:
                pass

    if prices:
        lowest = min(prices)
        print(f"Found prices: {sorted(set(prices))[:10]}... lowest={lowest}")
        return lowest
    print("No prices found in HTML")
    return None

def main():
    print("Starting price check...")
    price = get_price()

    if price is None:
        send_telegram(
            "⚠️ <b>Prijscheck mislukt</b>\n\n"
            "Kon de Kinguin-pagina niet ophalen (waarschijnlijk Cloudflare).\n"
            f"<a href='{PRODUCT_URL}'>Bekijk handmatig</a>"
        )
        sys.exit(1)

    msg = (
        f"ℹ️ <b>Prijscheck</b>\n\n"
        f"PSN EUR 100 Gift Card NL\n"
        f"Laagste prijs nu: <b>€{price:.2f}</b>\n"
        f"Target: ≤ €{TARGET_PRICE}\n\n"
        f"<a href='{PRODUCT_URL}'>Bekijk op Kinguin</a>"
    )

    if price <= TARGET_PRICE:
        msg = (
            f"🔥 <b>PRIJSALERT!</b>\n\n"
            f"PSN EUR 100 Gift Card NL is nu <b>€{price:.2f}</b>\n"
            f"Target was €{TARGET_PRICE}\n\n"
            f"<a href='{PRODUCT_URL}'>➡️ Koop nu</a>"
        )
        print("ALERT TRIGGERED")
    else:
        print(f"Price €{price:.2f} is above target")

    send_telegram(msg)

if __name__ == "__main__":
    main()

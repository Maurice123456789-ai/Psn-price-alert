#!/usr/bin/env python3

import os
import re
import sys
import requests
from playwright.sync_api import sync_playwright

PRODUCT_URL = "https://www.kinguin.net/category/95893/playstation-network-eur-100-gift-card-nl"
TARGET_PRICE_EUR = 87.00

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")


def send_telegram(message):
    if not BOT_TOKEN or not CHAT_ID:
        print("Telegram configuratie ontbreekt")
        return False

    response = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={
            "chat_id": CHAT_ID,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
        },
        timeout=20,
    )
    print("Telegram status:", response.status_code)
    return response.ok


def get_usd_to_eur_rate():
    response = requests.get(
        "https://api.frankfurter.app/latest?from=USD&to=EUR",
        timeout=20,
    )
    response.raise_for_status()
    return float(response.json()["rates"]["EUR"])


def extract_product_price_usd(text):
    title = "PlayStation Network EUR 100 Gift Card NL"

    start = text.find(title)
    if start == -1:
        print("Producttitel niet gevonden")
        return None

    end = text.find("BUY WITH", start)
    if end == -1:
        end = start + 3000

    section = text[start:end]

    prices = re.findall(r"\$(\d+\.\d{2})", section)
    print("Prijzen gevonden:", prices)

    if len(prices) < 2:
        return None

    return float(prices[1])


def get_price_eur():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )

        page = browser.new_page()

        try:
            response = page.goto(
                PRODUCT_URL,
                wait_until="domcontentloaded",
                timeout=60000,
            )

            if response:
                print("HTTP status:", response.status)

            page.wait_for_timeout(10000)

            text = page.locator("body").inner_text()

            with open("kinguin_debug.txt", "w", encoding="utf-8") as f:
                f.write(text)

            usd_price = extract_product_price_usd(text)

            if usd_price is None:
                return None

            eur_rate = get_usd_to_eur_rate()
            return usd_price * eur_rate

        finally:
            browser.close()


def main():
    price_eur = get_price_eur()

    if price_eur is None:
        print("Prijs kon niet worden bepaald")
        sys.exit(1)

    print(f"Huidige prijs: €{price_eur:.2f}")

    if price_eur <= TARGET_PRICE_EUR:
        send_telegram(
            "🔥 <b>PRIJSALERT!</b>\n\n"
            "🎮 PSN EUR 100 Gift Card NL\n\n"
            f"💰 Prijs: <b>€{price_eur:.2f}</b>\n"
            f"🎯 Target: €{TARGET_PRICE_EUR:.2f}\n\n"
            f"{PRODUCT_URL}"
        )
    else:
        print(f"Geen alert: €{price_eur:.2f} > €{TARGET_PRICE_EUR:.2f}")


if __name__ == "__main__":
    main()

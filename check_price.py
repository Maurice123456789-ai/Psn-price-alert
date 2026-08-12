#!/usr/bin/env python3

import os
import re
import sys
import requests

from playwright.sync_api import sync_playwright

PRODUCT_URL = (
    "https://www.kinguin.net/category/95893/"
    "playstation-network-eur-100-gift-card-nl"
)

TARGET_PRICE_EUR = 87.00

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")


def send_telegram(message):
    response = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={
            "chat_id": CHAT_ID,
            "text": message,
            "parse_mode": "HTML",
        },
        timeout=20,
    )
    return response.ok


def get_usd_to_eur_rate():
    data = requests.get(
        "https://api.frankfurter.app/latest?from=USD&to=EUR",
        timeout=20,
    ).json()

    return float(data["rates"]["EUR"])


def extract_product_price_usd(text):
    title_pos = text.find(
        "PlayStation Network EUR 100 Gift Card NL"
    )

    if title_pos == -1:
        return None

    buy_pos = text.find("BUY WITH", title_pos)

    if buy_pos == -1:
        return None

    section = text[title_pos:buy_pos]

    prices = re.findall(r"\$(\d+\.\d{2})", section)

    if len(prices) < 2:
        return None

    # Eerste prijs = doorgestreepte prijs
    # Tweede prijs = actuele prijs
    return float(prices[1])


def get_price_eur():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox"]
        )

        page = browser.new_page()

        try:
            page.goto(
                PRODUCT_URL,
                wait_until="networkidle",
                timeout=90000
            )

            page.wait_for_timeout(5000)

            text = page.locator("body").inner_text()

            with open(
                "kinguin_debug.txt",
                "w",
                encoding="utf-8"
            ) as f:
                f.write(text)

            usd_price = extract_product_price_usd(text)

            if usd_price is None:
                return None

            rate = get_usd_to_eur_rate()

            return usd_price * rate

        finally:
            browser.close()


def main():
    price_eur = get_price_eur()

    if price_eur is None:
        print("Prijs niet gevonden")
        sys.exit(1)

    print(f"Prijs: €{price_eur:.2f}")

    if price_eur <= TARGET_PRICE_EUR:
        send_telegram(
            "🔥 <b>PRIJSALERT!</b>\n\n"
            f"💰 Prijs: €{price_eur:.2f}\n"
            f"🎯 Target: €{TARGET_PRICE_EUR:.2f}\n\n"
            f"{PRODUCT_URL}"
        )


if __name__ == "__main__":
    main()

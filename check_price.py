#!/usr/bin/env python3

import os
import re
import sys
import requests

from playwright.sync_api import (
    sync_playwright,
    TimeoutError as PlaywrightTimeoutError
)

PRODUCT_URL = (
    "https://www.kinguin.net/category/95893/"
    "playstation-network-eur-100-gift-card-nl"
)

TARGET_PRICE_EUR = 87.00

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")


def send_telegram(message):
    if not BOT_TOKEN or not CHAT_ID:
        return False

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


def parse_price(text):
    match = re.search(r"(\d+[.,]\d{2})", text)
    if not match:
        return None
    return float(match.group(1).replace(",", "."))


def extract_product_price(page):
    selectors = [
        '[data-testid*="price"]',
        '[class*="price"]',
        '[class*="Price"]',
        'span[class*="price"]',
        'div[class*="price"]',
    ]

    candidates = []

    for selector in selectors:
        try:
            elements = page.locator(selector)
            count = min(elements.count(), 20)

            for i in range(count):
                try:
                    txt = elements.nth(i).inner_text().strip()
                    price = parse_price(txt)

                    if price is not None and 70 <= price <= 130:
                        candidates.append(price)
                except Exception:
                    pass
        except Exception:
            pass

    if not candidates:
        return None

    return sorted(candidates)[0]


def get_price():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )

        page = browser.new_page()

        try:
            page.goto(
                PRODUCT_URL,
                wait_until="networkidle",
                timeout=90000,
            )

            page.wait_for_timeout(8000)

            price = extract_product_price(page)
            return price

        finally:
            browser.close()


def main():
    price = get_price()

    if price is None:
        sys.exit(1)

    if price <= TARGET_PRICE_EUR:
        send_telegram(
            f"🔥 PRIJSALERT!\n\n"
            f"Prijs: €{price:.2f}\n"
            f"Target: €{TARGET_PRICE_EUR:.2f}\n\n"
            f"{PRODUCT_URL}"
        )


if __name__ == "__main__":
    main()

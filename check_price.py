#!/usr/bin/env python3

import os
import re
import sys
import requests

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


PRODUCT_URL = (
    "https://www.kinguin.net/category/95893/"
    "playstation-network-eur-100-gift-card-nl"
)

TARGET_PRICE = 87.00

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")


def send_telegram(message):
    if not BOT_TOKEN:
        print("ERROR: TELEGRAM_BOT_TOKEN ontbreekt")
        return False

    if not CHAT_ID:
        print("ERROR: TELEGRAM_CHAT_ID ontbreekt")
        return False

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }

    try:
        response = requests.post(
            url,
            json=payload,
            timeout=20,
        )

        print(f"Telegram response: {response.status_code}")

        if response.status_code != 200:
            print(f"Telegram error: {response.text}")
            return False

        data = response.json()

        if not data.get("ok"):
            print(f"Telegram API error: {data}")
            return False

        print("Telegram bericht verzonden")
        return True

    except Exception as e:
        print(f"Telegram request failed: {e}")
        return False


def extract_prices(text):
    prices = []

    patterns = [
        r"€\s*(\d{1,3}[.,]\d{2})",
        r"(\d{1,3}[.,]\d{2})\s*€",
        r"(\d{1,3}[.,]\d{2})\s*EUR",
    ]

    for pattern in patterns:
        for match in re.findall(pattern, text, re.IGNORECASE):
            try:
                price = float(match.replace(",", "."))

                # Realistische prijzen voor een €100 PSN-kaart
                if 60.00 <= price <= 140.00:
                    prices.append(price)

            except ValueError:
                pass

    return sorted(set(prices))


def get_price():
    print("Starting Kinguin browser check...")

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
            ],
        )

        context = browser.new_context(
            locale="nl-NL",
            timezone_id="Europe/Amsterdam",
            viewport={
                "width": 1366,
                "height": 900,
            },
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
        )

        page = context.new_page()

        try:
            response = page.goto(
                PRODUCT_URL,
                wait_until="domcontentloaded",
                timeout=60000,
            )

            if response:
                print(f"Kinguin HTTP status: {response.status}")

            # Kinguin kan de prijs pas later met JavaScript tonen.
            page.wait_for_timeout(10000)

            text = page.locator("body").inner_text()

            print(f"Page text: {len(text)} characters")

            # Debugbestand bewaren
            with open(
                "kinguin_debug.txt",
                "w",
                encoding="utf-8",
            ) as f:
                f.write(text)

            lower = text.lower()

            # Detecteer Cloudflare challenge
            cloudflare_signs = [
                "checking your browser",
                "verify you are human",
                "just a moment",
                "cloudflare",
                "security check",
            ]

            if any(sign in lower for sign in cloudflare_signs):
                print("Cloudflare challenge detected")
                return None

            prices = extract_prices(text)

            print(f"Prices found: {prices}")

            if not prices:
                print("Geen prijzen gevonden")
                return None

            lowest = min(prices)

            print(f"Lowest price found: €{lowest:.2f}")

            return lowest

        except PlaywrightTimeoutError:
            print("Kinguin page loading timeout")
            return None

        except Exception as e:
            print(f"Browser error: {e}")
            return None

        finally:
            browser.close()


def main():
    print("================================")
    print("Kinguin PSN Price Checker")
    print("================================")
    print(f"Target: €{TARGET_PRICE:.2f}")

    price = get_price()

    if price is None:
        print("Prijs kon niet worden bepaald.")
        print("Waarschijnlijk Cloudflare of gewijzigde pagina.")
        sys.exit(1)

    print(f"Current price: €{price:.2f}")

    if price <= TARGET_PRICE:

        print("🔥 PRICE ALERT!")

        message = (
            "🔥 <b>PRIJSALERT!</b>\n\n"
            "🎮 PSN EUR 100 Gift Card NL\n\n"
            f"💰 Prijs: <b>€{price:.2f}</b>\n"
            f"🎯 Target: €{TARGET_PRICE:.2f}\n\n"
            f'<a href="{PRODUCT_URL}">➡️ KOOP NU BIJ KINGUIN</a>'
        )

        if not send_telegram(message):
            sys.exit(1)

    else:

        print(
            f"€{price:.2f} is hoger dan target "
            f"€{TARGET_PRICE:.2f}"
        )

        # Geen Telegrambericht boven de targetprijs.


if __name__ == "__main__":
    main()        )

        context = browser.new_context(
            locale="nl-NL",
            timezone_id="Europe/Amsterdam",
            viewport={
                "width": 1366,
                "height": 900,
            },
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
        )

        page = context.new_page()

        try:
            response = page.goto(
                PRODUCT_URL,
                wait_until="domcontentloaded",
                timeout=60000,
            )

            if response:
                print(f"Kinguin HTTP status: {response.status}")

            # Even after domcontentloaded Kinguin may still be
            # rendering prices with JavaScript.
            page.wait_for_timeout(10000)

            text = page.locator("body").inner_text()

            print(f"Page text: {len(text)} characters")

            # Debugbestand bewaren als artifact/log indien nodig
            with open(
                "kinguin_debug.txt",
                "w",
                encoding="utf-8",
            ) as f:
                f.write(text)

            lower = text.lower()

            # Detecteer Cloudflare challenge
            cloudflare_signs = [
                "checking your browser",
                "verify you are human",
                "just a moment",
                "cloudflare",
                "security check",
            ]

            if any(sign in lower for sign in cloudflare_signs):
                print("Cloudflare challenge detected")
                return None

            prices = extract_prices(text)

            print(f"Prices found: {prices}")

            if not prices:
                print("Geen prijzen gevonden")
                return None

            lowest = min(prices)

            print(f"Lowest price found: €{lowest:.2f}")

            return lowest

        except PlaywrightTimeoutError:
            print("Kinguin page loading timeout")
            return None

        except Exception as e:
            print(f"Browser error: {e}")
            return None

        finally:
            browser.close()


def main():
    print("================================")
    print("Kinguin PSN Price Checker")
    print("================================")
    print(f"Target: €{TARGET_PRICE:.2f}")

    price = get_price()

    if price is None:
        print("Prijs kon niet worden bepaald.")
        print("Waarschijnlijk Cloudflare of gewijzigde pagina.")
        sys.exit(1)

    print(f"Current price: €{price:.2f}")

    if price <= TARGET_PRICE:

        print("🔥 PRICE ALERT!")

        message = (
            "🔥 <b>PRIJSALERT!</b>\n\n"
            "🎮 PSN EUR 100 Gift Card NL\n\n"
            f"💰 Prijs: <b>€{price:.2f}</b>\n"
            f"🎯 Target: €{TARGET_PRICE:.2f}\n\n"
            f"<a href=\"{PRODUCT_URL}\">➡️ KOOP NU BIJ KINGUIN</a>"
        )

        if not send_telegram(message):
            sys.exit(1)

    else:

        print(
            f"€{price:.2f} is hoger dan target "
            f"€{TARGET_PRICE:.2f}"
        )

        # Geen Telegrambericht boven de targetprijs.


if __name__ == "__main__":
    main()
```
    main()

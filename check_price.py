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

TARGET_PRICE_EUR = 87.00

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


def get_usd_to_eur_rate():
    print("USD -> EUR wisselkoers ophalen...")

    try:
        response = requests.get(
            "https://api.frankfurter.app/latest?from=USD&to=EUR",
            timeout=20,
        )

        response.raise_for_status()

        data = response.json()
        rate = float(data["rates"]["EUR"])

        print(f"USD -> EUR koers: {rate:.6f}")

        return rate

    except Exception as e:
        print(f"Kon USD -> EUR wisselkoers niet ophalen: {e}")
        return None


def extract_prices(text):
    eur_prices = []
    usd_prices = []

    # Europrijzen zoals:
    # €87.00
    # €87,00
    # 87.00 €
    # 87,00 EUR
    euro_patterns = [
        r"€\s*(\d{1,3}(?:[.,]\d{2}))",
        r"(\d{1,3}(?:[.,]\d{2}))\s*€",
        r"(\d{1,3}(?:[.,]\d{2}))\s*EUR",
    ]

    for pattern in euro_patterns:
        for match in re.findall(pattern, text, re.IGNORECASE):
            try:
                price = float(match.replace(",", "."))

                if 60.00 <= price <= 140.00:
                    eur_prices.append(price)

            except ValueError:
                pass

    # Dollarprijzen zoals:
    # $112.39
    # $107.89
    # 112.39 USD
    usd_patterns = [
        r"\$\s*(\d{1,3}(?:[.,]\d{2}))",
        r"(\d{1,3}(?:[.,]\d{2}))\s*USD",
    ]

    for pattern in usd_patterns:
        for match in re.findall(pattern, text, re.IGNORECASE):
            try:
                price = float(match.replace(",", "."))

                if 60.00 <= price <= 160.00:
                    usd_prices.append(price)

            except ValueError:
                pass

    return sorted(set(eur_prices)), sorted(set(usd_prices))


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
            print("Opening Kinguin...")

            response = page.goto(
                PRODUCT_URL,
                wait_until="domcontentloaded",
                timeout=60000,
            )

            if response:
                print(f"Kinguin HTTP status: {response.status}")

            # Geef JavaScript voldoende tijd om prijzen te laden.
            page.wait_for_timeout(10000)

            text = page.locator("body").inner_text()

            print(f"Page text: {len(text)} characters")

            # Debugbestand bewaren.
            with open(
                "kinguin_debug.txt",
                "w",
                encoding="utf-8",
            ) as f:
                f.write(text)

            lower = text.lower()

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

            eur_prices, usd_prices = extract_prices(text)

            print(f"EUR prices found: {eur_prices}")
            print(f"USD prices found: {usd_prices}")

            # Als er EUR-prijzen gevonden worden, gebruiken we die.
            if eur_prices:
                lowest = min(eur_prices)

                print(f"Lowest EUR price found: €{lowest:.2f}")

                return lowest

            # Geen EUR maar wel USD gevonden:
            if usd_prices:
                usd_rate = get_usd_to_eur_rate()

                if usd_rate is None:
                    print("USD-prijs gevonden, maar conversie naar EUR mislukt.")
                    return None

                converted_prices = [
                    price * usd_rate
                    for price in usd_prices
                ]

                print(
                    "USD prijzen omgerekend naar EUR: "
                    + ", ".join(
                        f"${usd:.2f} -> €{eur:.2f}"
                        for usd, eur in zip(
                            usd_prices,
                            converted_prices,
                        )
                    )
                )

                lowest_eur = min(converted_prices)

                print(
                    f"Laagste omgerekende prijs: "
                    f"€{lowest_eur:.2f}"
                )

                return lowest_eur

            print("Geen EUR- of USD-prijzen gevonden.")
            return None

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
    print(f"Target: €{TARGET_PRICE_EUR:.2f}")

    price_eur = get_price()

    if price_eur is None:
        print("Prijs kon niet worden bepaald.")
        sys.exit(1)

    print(f"Current price in EUR: €{price_eur:.2f}")

    if price_eur <= TARGET_PRICE_EUR:
        print("🔥 PRICE ALERT!")

        message = (
            "🔥 <b>PRIJSALERT!</b>\n\n"
            "🎮 PSN EUR 100 Gift Card NL\n\n"
            f"💰 Prijs: <b>€{price_eur:.2f}</b>\n"
            f"🎯 Target: €{TARGET_PRICE_EUR:.2f}\n\n"
            f'<a href="{PRODUCT_URL}">➡️ KOOP NU BIJ KINGUIN</a>'
        )

        if not send_telegram(message):
            sys.exit(1)

    else:
        print(
            f"€{price_eur:.2f} is hoger dan target "
            f"€{TARGET_PRICE_EUR:.2f}"
        )


if __name__ == "__main__":
    main()

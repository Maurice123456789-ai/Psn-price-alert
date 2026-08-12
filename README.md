# Kinguin PSN Price Alert (GitHub Actions)

Dit project controleert elke 30 minuten de prijs van de **PlayStation Network EUR 100 Gift Card NL** op Kinguin en stuurt een Telegram-bericht via jouw bot.

## Hoe instellen (eenvoudig)

### 1. Maak een nieuw GitHub repository
1. Ga naar https://github.com/new
2. Geef het een naam, bijv. `psn-price-alert`
3. Kies **Public** (gratis) of Private
4. Klik **Create repository**

### 2. Upload de bestanden
Upload deze 3 bestanden naar je repository:
- `check_price.py`
- `.github/workflows/price-check.yml`
- `README.md` (optioneel)

Je kunt ze drag-and-drop uploaden via de GitHub website.

### 3. Voeg je bot-token toe als Secret
1. Ga in je repository naar **Settings** → **Secrets and variables** → **Actions**
2. Klik **New repository secret**
3. Name: `TELEGRAM_BOT_TOKEN`
4. Value: plak hier je bot-token (`8853986384:AAFGlkJQS4XVvQEFec2kMOFx6B27YZEQKR0`)
5. Klik **Add secret**

Optioneel nog een secret:
- Name: `TELEGRAM_CHAT_ID`
- Value: `6571415052`

### 4. Activeer de workflow
1. Ga naar het tabblad **Actions**
2. Klik op de workflow "Kinguin PSN Price Check"
3. Klik op **Run workflow** (handmatige test)
4. Daarna draait hij automatisch elke 30 minuten

### Belangrijk
- Cloudflare van Kinguin kan de check soms blokkeren. Dan krijg je een “mislukt”-bericht.
- GitHub Actions is gratis voor openbare repositories (binnen redelijke limieten).
- Na 48 uur kun je de workflow uitzetten via Actions → Disable workflow.

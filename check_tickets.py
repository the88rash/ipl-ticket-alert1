import os
import requests
from bs4 import BeautifulSoup

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

# District.in page for DC vs CSK May
URL = "https://www.district.in/events/ipl-ticket-booking"

KEYWORDS_LIVE = ["sale is live", "book tickets", "book now", "buy tickets"]
KEYWORDS_WAITING = ["tickets available in", "coming soon", "notify me", "sale begins"]


def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    response = requests.post(url, json=payload)
    response.raise_for_status()
    print("Telegram message sent!")


def check_tickets():
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    response = requests.get(URL, headers=headers, timeout=15)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    page_text = soup.get_text().lower()

    # Look for the DC vs CSK May section specifically
    csk_section = ""
    for block in soup.find_all(string=lambda t: t and ("super kings" in t.lower() or "csk" in t.lower())):
        parent = block.find_parent()
        if parent:
            csk_section += parent.get_text().lower() + " "

    # Check the CSK section first, fall back to full page
    search_text = csk_section if csk_section else page_text

    is_live = any(kw in search_text for kw in KEYWORDS_LIVE)
    is_waiting = any(kw in search_text for kw in KEYWORDS_WAITING)

    print(f"Page fetched. CSK sectiON found: {bool(csk_section)}")
    print(f"Is live: {is_live} | Is waiting: {is_waiting}")

    if is_live and not is_waiting:
        send_telegram(
            "🚨 *IPL TICKETS ARE LIVE!* 🚨\n\n"
            "🏏 *DC vs CSK — May*\n"
            "📍 Arun Jaitley Stadium, Delhi\n\n"
            "👉 Book NOW before they sell out:\n"
            "https://www.district.in/events/delhi-capitals-team\n\n"
            "⚡ You have only 10 mins once you select seats!"
        )
        return True
    else:
        print("Tickets not live yet. Status: Coming Soon / Notify Me")
        return False


if __name__ == "__main__":
    check_tickets()

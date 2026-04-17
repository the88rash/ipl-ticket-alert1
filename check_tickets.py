import os
import requests
from bs4 import BeautifulSoup

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

# District.in page for DC vs RCB April 27
URL = "https://www.district.in/events/tata-ipl-2026-match-39--delhi-capitals-vs-royal-challengers-bengaluru-buy-tickets"

KEYWORDS_LIVE = ["sale is live", "pre-sale is live", "book now", "buy tickets"]
KEYWORDS_WAITING = ["tickets available in", "coming soon"]
KEYWORDS_NOT_OPEN_YET = ["be the first to know when sale begins"]


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

    # Look for the DC vs RCB April 27 section specifically
    rcb_section = ""
    for block in soup.find_all(string=lambda t: t and ("royal challengers" in t.lower() or "rcb" in t.lower())):
        parent = block.find_parent()
        if parent:
            rcb_section += parent.get_text().lower() + " "

    # Check the RCB section first, fall back to full page
    search_text = page_text

    is_live = any(kw in search_text for kw in KEYWORDS_LIVE)
    is_waiting = any(kw in search_text for kw in KEYWORDS_WAITING)
    is_not_open_yet = any(kw in search_text for kw in KEYWORDS_NOT_OPEN_YET)

    print(f"Page Text: {page_text}")
    print(f"Page fetched. RCB sectION found: {bool(rcb_section)}")
    print(f"Is live: {is_live} | Is waiting: {is_waiting} | Is not open yet: {is_not_open_yet}")

    if is_live and not is_waiting:
        send_telegram(
            "🚨 *YOUR PREFERRED IPL TICKETS ARE LIVE!* 🚨\n\n"
            "👉 Book NOW before they sell out:\n"
            "https://www.district.in/events/ipl-ticket-booking\n"
            "⚡ You have only 10 mins once you select seats!"
        )
        return True
    elif is_waiting:
        send_telegram(
            "🚨 *YOUR PREFERRED IPL TICKETS ARE COMING SOON!* 🚨\n\n"
            "👉 SET A REMINDER ON PHONE:\n"
            "https://www.district.in/events/ipl-ticket-booking"
        )
        return False
    else:
        print("Tickets not live yet.")
        return False


if __name__ == "__main__":
    check_tickets()

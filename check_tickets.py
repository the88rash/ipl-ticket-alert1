import os
import requests
from bs4 import BeautifulSoup

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

KEYWORDS_LIVE = ["sale is live", "pre-sale is live", "book now", "buy tickets"]
KEYWORDS_WAITING = ["tickets available in", "coming soon"]
KEYWORDS_NOT_OPEN_YET = ["be the first to know when sale begins"]

URLS_FILE = "urls.txt"
IPL_BOOKING_URL = "https://www.district.in/events/ipl-ticket-booking"


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


def get_match_title(page_text):
    """Extract first non-empty line from page text as match title."""
    for line in page_text.splitlines():
        line = line.strip()
        if line:
            return line[:100]  # cap at 100 chars
    return "Unknown Match"


def check_url(url):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    page_text = soup.get_text()
    page_text_lower = page_text.lower()

    match_title = get_match_title(page_text)

    is_live = any(kw in page_text_lower for kw in KEYWORDS_LIVE)
    is_waiting = any(kw in page_text_lower for kw in KEYWORDS_WAITING)
    is_not_open_yet = any(kw in page_text_lower for kw in KEYWORDS_NOT_OPEN_YET)

    print(f"URL: {url}")
    print(f"Match title: {match_title}")
    print(f"Is live: {is_live} | Is waiting: {is_waiting} | Is not open yet: {is_not_open_yet}")

    if is_live and not is_waiting:
        send_telegram(
            "🚨 *YOUR PREFERRED IPL TICKETS ARE LIVE!* 🚨\n\n"
            f"🏏 *{match_title}*\n\n"
            f"👉 Book NOW before they sell out:\n{url}\n\n"
            f"🎟️ All IPL matches:\n{IPL_BOOKING_URL}\n\n"
            "⚡ You have only 10 mins once you select seats!"
        )
        return True
    elif is_waiting:
        send_telegram(
            "🚨 *YOUR PREFERRED IPL TICKETS ARE COMING SOON!* 🚨\n\n"
            f"🏏 *{match_title}*\n\n"
            f"👉 SET A REMINDER ON PHONE:\n{url}\n\n"
            f"🎟️ All IPL matches:\n{IPL_BOOKING_URL}"
        )
        return False
    elif is_not_open_yet:
        print("Sale not open yet.")
        return False
    else:
        print("Tickets not live yet.")
        return False


def load_urls():
    if not os.path.exists(URLS_FILE):
        print(f"{URLS_FILE} not found — nothing to check.")
        return []
    with open(URLS_FILE) as f:
        urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    print(f"Loaded {len(urls)} URL(s) to check.")
    return urls


if __name__ == "__main__":
    urls = load_urls()
    for url in urls:
        check_url(url)

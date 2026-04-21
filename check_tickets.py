import os
import requests
from bs4 import BeautifulSoup

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

# Keywords for District by Zomato
DISTRICT_KEYWORDS_LIVE = ["sale is live", "pre-sale is live", "book now", "buy tickets", "book tickets"]
DISTRICT_KEYWORDS_WAITING = ["tickets available in", "coming soon"]
DISTRICT_KEYWORDS_NOT_OPEN_YET = ["be the first to know when sale begins"]

# Keywords for BookMyShow
BMS_KEYWORDS_LIVE = ["book now", "login to book"]
BMS_KEYWORDS_WAITING = ["coming soon"]
BMS_KEYWORDS_NOT_OPEN_YET = ["coming soon"]

# Keywords for RCB website
# RCB uses a single listing page — we search for the match name near a live keyword
RCB_KEYWORDS_LIVE = ["buy tickets", "book now", "add to cart"]
RCB_KEYWORDS_WAITING = ["coming soon", "notify me", "register interest"]
RCB_KEYWORDS_NOT_OPEN_YET = ["coming soon"]

URLS_FILE = "urls.txt"
IPL_BOOKING_URL_DISTRICT = "https://www.district.in/events/ipl-ticket-booking"
IPL_BOOKING_URL_BMS = "https://in.bookmyshow.com/sports/ipl-2026"
IPL_BOOKING_URL_RCB = "https://shop.royalchallengers.com/ticket"


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
            return line[:100]
    return "Unknown Match"


def is_bookmyshow_url(url):
    return "bookmyshow.com" in url


def is_rcb_url(url):
    return "royalchallengers.com" in url


def extract_rcb_match_info(raw_url):
    """
    RCB entries in urls.txt use pipe-separated format:
      https://shop.royalchallengers.com/ticket|RCB vs GT|24 Apr 2026
    Returns (page_url, match_label, match_date).
    """
    parts = raw_url.split("|")
    if len(parts) == 3:
        return parts[0].strip(), parts[1].strip(), parts[2].strip()
    return raw_url, None, None


def check_rcb_match(raw_url):
    """
    RCB uses a single listing page for all home matches.
    We fetch shop.royalchallengers.com/ticket, find the specific match
    by name, then check if 'buy tickets' appears near it in the page.
    """
    page_url, match_label, match_date = extract_rcb_match_info(raw_url)

    if not match_label:
        print("RCB URL missing match label — cannot do precise check.")
        send_telegram(
            "⚠️ RCB match URL is missing match info.\n"
            "Please re-add it in this format:\n"
            "`https://shop.royalchallengers.com/ticket|RCB vs GT|24 Apr 2026`"
        )
        return False

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    response = requests.get(page_url, headers=headers, timeout=15)

    if response.status_code == 403:
        print("403 Forbidden — RCB site is blocking automated requests.")
        send_telegram(
            "⚠️ *Could not check RCB tickets* — site is blocking automated requests.\n\n"
            f"🔗 Please check manually:\n{page_url}"
        )
        return False

    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    page_lower = soup.get_text(separator="\n").lower()

    print(f"RCB page fetched. Looking for match: {match_label!r}")

    # Find the match by label in the page
    match_label_lower = match_label.lower()
    idx = page_lower.find(match_label_lower)

    if idx == -1:
        # Fallback: try just the away team name (e.g. "GT" or "Gujarat Titans")
        away_team = match_label.split("vs")[-1].strip().lower()
        idx = page_lower.find(away_team)
        print(f"  Full label not found. Trying away team '{away_team}' — idx: {idx}")

    if idx == -1:
        print("  Match not found on RCB page — may not be listed yet.")
        return False

    # Check 500 chars around the match for live/waiting keywords
    surrounding = page_lower[max(0, idx - 100): idx + 400]
    print(f"  Snippet: {surrounding[:200]!r}")

    is_live = any(kw in surrounding for kw in RCB_KEYWORDS_LIVE)
    is_waiting = any(kw in surrounding for kw in RCB_KEYWORDS_WAITING)
    is_not_open_yet = any(kw in surrounding for kw in RCB_KEYWORDS_NOT_OPEN_YET)

    print(f"  Is live: {is_live} | Is waiting: {is_waiting} | Is not open yet: {is_not_open_yet}")

    if is_live and not is_waiting and not is_not_open_yet:
        send_telegram(
            "*YOUR IPL TICKETS ARE LIVE!* 🚨\n\n"
            f"{match_label} {match_date}\n"
            f"Book NOW before they sell out:\n{page_url}\n\n"
            f"All RCB matches:\n{IPL_BOOKING_URL_RCB}\n\n"
            "⚡ You have only 10 mins once you select seats!"
        )
        return True
    elif is_waiting and not is_not_open_yet:
        send_telegram(
            "*YOUR IPL TICKETS ARE COMING SOON!* ⏲️\n\n"
            f"{match_label} {match_date}\n"
            f"SET A REMINDER:\n{page_url}\n\n"
            f"All RCB matches:\n{IPL_BOOKING_URL_RCB}"
        )
        return False
    else:
        print("RCB tickets not live yet for this match.")
        return False


def check_url(url):
    # RCB matches use pipe-separated format: url|match_label|date
    if is_rcb_url(url.split("|")[0]):
        return check_rcb_match(url)

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }
    response = requests.get(url, headers=headers, timeout=15)

    if response.status_code == 403:
        print(f"403 Forbidden — {url} is blocking automated requests.")
        send_telegram(
            f"⚠️ *Could not check this URL* — the site is blocking automated requests.\n\n"
            f"🔗 Please check manually:\n{url}"
        )
        return False

    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    page_text = soup.get_text()
    page_text_lower = page_text.lower()

    match_title = get_match_title(page_text)

    # Pick keywords and booking URL based on platform
    if is_bookmyshow_url(url):
        keywords_live = BMS_KEYWORDS_LIVE
        keywords_waiting = BMS_KEYWORDS_WAITING
        keywords_not_open_yet = BMS_KEYWORDS_NOT_OPEN_YET
        all_ipl_url = IPL_BOOKING_URL_BMS
        platform = "BookMyShow"
    else:
        keywords_live = DISTRICT_KEYWORDS_LIVE
        keywords_waiting = DISTRICT_KEYWORDS_WAITING
        keywords_not_open_yet = DISTRICT_KEYWORDS_NOT_OPEN_YET
        all_ipl_url = IPL_BOOKING_URL_DISTRICT
        platform = "District by Zomato"

    is_live = any(kw in page_text_lower for kw in keywords_live)
    is_waiting = any(kw in page_text_lower for kw in keywords_waiting)
    is_not_open_yet = any(kw in page_text_lower for kw in keywords_not_open_yet)

    print(f"URL: {url}")
    print(f"Platform: {platform}")
    print(f"Match title: {match_title}")
    print(f"Is live: {is_live} | Is waiting: {is_waiting} | Is not open yet: {is_not_open_yet}")

    if is_live and not is_waiting and not is_not_open_yet:
        send_telegram(
            " *YOUR IPL TICKETS ARE LIVE!* 🚨\n\n"
            f" {match_title}\n"
            f" Platform: {platform}\n\n"
            f" Book NOW before they sell out:\n{url}\n\n"
            f" All IPL matches:\n{all_ipl_url}\n\n"
            "⚡ You have only 10 mins once you select seats!"
        )
        return True
    elif is_waiting:
        send_telegram(
            " *YOUR IPL TICKETS ARE COMING SOON!* ⏲️\n\n"
            f" {match_title}\n"
            f" Platform: {platform}\n\n"
            f" Set a REMINDER on phone:\n{url}\n\n"
            f" All IPL matches:\n{all_ipl_url}"
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
        try:
            check_url(url)
        except Exception as e:
            print(f"Error checking {url}: {e}")
            send_telegram(f"⚠️ Error checking URL:\n`{url}`\n{str(e)[:100]}")

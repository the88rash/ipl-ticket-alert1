import os
import re
import requests
from bs4 import BeautifulSoup
from difflib import SequenceMatcher

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
URLS_FILE = "urls.txt"
OFFSET_FILE = ".last_update_id"

DISTRICT_KEYWORDS_LIVE = ["sale is live", "pre-sale is live", "book now", "buy tickets"]
DISTRICT_KEYWORDS_WAITING = ["tickets available in", "coming soon"]
DISTRICT_KEYWORDS_NOT_OPEN_YET = ["be the first to know when sale begins"]

BMS_KEYWORDS_LIVE = ["book now", "login to book"]
BMS_KEYWORDS_WAITING = ["coming soon"]
BMS_KEYWORDS_NOT_OPEN_YET = ["coming soon"]

IPL_BOOKING_URL_DISTRICT = "https://www.district.in/events/ipl-ticket-booking"
IPL_BOOKING_URL_BMS = "https://in.bookmyshow.com/sports/ipl-2026"
DISTRICT_IPL_LISTING = "https://www.district.in/events/ipl-ticket-booking"

# Team name aliases for fuzzy matching
TEAM_ALIASES = {
    # Abbreviations
    "dc": "delhi capitals",
    "rcb": "royal challengers bengaluru",
    "mi": "mumbai indians",
    "csk": "chennai super kings",
    "kkr": "kolkata knight riders",
    "srh": "sunrisers hyderabad",
    "rr": "rajasthan royals",
    "pbks": "punjab kings",
    "lsg": "lucknow super giants",
    "gt": "gujarat titans",
    # City names
    "delhi": "delhi capitals",
    "bangalore": "royal challengers bengaluru",
    "bengaluru": "royal challengers bengaluru",
    "mumbai": "mumbai indians",
    "chennai": "chennai super kings",
    "kolkata": "kolkata knight riders",
    "hyderabad": "sunrisers hyderabad",
    "rajasthan": "rajasthan royals",
    "punjab": "punjab kings",
    "lucknow": "lucknow super giants",
    "gujarat": "gujarat titans",
    # Partial team names
    "capitals": "delhi capitals",
    "challengers": "royal challengers bengaluru",
    "royal challengers": "royal challengers bengaluru",
    "indians": "mumbai indians",
    "super kings": "chennai super kings",
    "kings": "chennai super kings",
    "knight riders": "kolkata knight riders",
    "knights": "kolkata knight riders",
    "sunrisers": "sunrisers hyderabad",
    "royals": "rajasthan royals",
    "titans": "gujarat titans",
    "super giants": "lucknow super giants",
    "giants": "lucknow super giants",
}

MONTH_ALIASES = {
    "jan": "jan", "january": "jan",
    "feb": "feb", "february": "feb",
    "mar": "mar", "march": "mar",
    "apr": "apr", "april": "apr",
    "may": "may",
    "jun": "jun", "june": "jun",
    "jul": "jul", "july": "jul",
    "aug": "aug", "august": "aug",
    "sep": "sep", "september": "sep",
    "oct": "oct", "october": "oct",
    "nov": "nov", "november": "nov",
    "dec": "dec", "december": "dec",
}


def get_updates(offset=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    params = {"timeout": 5}
    if offset:
        params["offset"] = offset
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    return response.json().get("result", [])


def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    requests.post(url, json=payload)


def load_urls():
    if not os.path.exists(URLS_FILE):
        return []
    with open(URLS_FILE) as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]


def save_urls(urls):
    with open(URLS_FILE, "w") as f:
        f.write("# URLs to check for ticket availability\n")
        for url in urls:
            f.write(url + "\n")


def load_offset():
    if not os.path.exists(OFFSET_FILE):
        return None
    with open(OFFSET_FILE) as f:
        return int(f.read().strip())


def save_offset(offset):
    with open(OFFSET_FILE, "w") as f:
        f.write(str(offset))


def is_valid_url(text):
    return (
        text.startswith("https://www.district.in") or
        text.startswith("https://district.in") or
        text.startswith("https://in.bookmyshow.com") or
        text.startswith("https://bookmyshow.com")
    )


def is_bookmyshow_url(url):
    return "bookmyshow.com" in url


def get_match_title(page_text):
    for line in page_text.splitlines():
        line = line.strip()
        if line:
            return line[:100]
    return "Unknown Match"


def normalize_query(text):
    """Expand team aliases and month names in the query."""
    text = text.lower()
    words = text.split()
    expanded = []
    for word in words:
        # Strip punctuation for lookup
        clean = re.sub(r'[^a-z]', '', word)
        if clean in TEAM_ALIASES:
            expanded.append(TEAM_ALIASES[clean])
        elif clean in MONTH_ALIASES:
            expanded.append(MONTH_ALIASES[clean])
        else:
            expanded.append(word)
    return " ".join(expanded)


def similarity(a, b):
    """Return similarity ratio between two strings."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def scrape_district_matches():
    """Scrape the District IPL listing page and return list of (title, url) tuples."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }
    try:
        response = requests.get(DISTRICT_IPL_LISTING, headers=headers, timeout=15)
        response.raise_for_status()
    except Exception as e:
        print(f"Failed to scrape District listing: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    matches = []

    # Find all links on the page that look like match event pages
    for a in soup.find_all("a", href=True):
        href = a["href"]
        # District match URLs contain "tata-ipl" or "ipl-2026"
        if "tata-ipl" in href or "ipl-2026" in href:
            full_url = href if href.startswith("http") else "https://www.district.in" + href
            title = a.get_text(strip=True)
            if title and len(title) > 5:
                matches.append((title, full_url))

    # Deduplicate by URL
    seen = set()
    unique = []
    for title, url in matches:
        if url not in seen:
            seen.add(url)
            unique.append((title, url))

    print(f"Found {len(unique)} matches on District listing page.")
    return unique


def find_match_from_query(query):
    """
    Given a natural language query, scrape District and find the best matching event.
    Returns (title, url) of best match, or None if no good match found.
    Also returns list of close candidates if ambiguous.
    """
    normalized_query = normalize_query(query)
    print(f"Normalized query: {normalized_query!r}")

    matches = scrape_district_matches()
    if not matches:
        return None, []

    scored = []
    for title, url in matches:
        score = similarity(normalized_query, title)
        # Also check if all query words appear in the title
        query_words = [w for w in normalized_query.split() if len(w) > 2]
        word_hits = sum(1 for w in query_words if w in title.lower())
        word_score = word_hits / max(len(query_words), 1)
        combined = (score + word_score) / 2
        scored.append((combined, title, url))
        print(f"  Score {combined:.2f} | {title}")

    scored.sort(reverse=True)

    best_score, best_title, best_url = scored[0]

    # Return best match if confident, or top 3 candidates if ambiguous
    if best_score >= 0.4:
        return (best_title, best_url), []
    elif best_score >= 0.25:
        candidates = [(t, u) for _, t, u in scored[:3]]
        return None, candidates
    else:
        return None, []


def run_status_check(urls):
    """Immediately check all tracked URLs and report status to Telegram."""
    if not urls:
        send_telegram("📋 No URLs being tracked yet. Send a district.in URL or describe a match!")
        return

    send_telegram(f"🔍 Checking {len(urls)} match(es) right now...")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    for url in urls:
        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            page_text = soup.get_text()
            page_text_lower = page_text.lower()
            match_title = get_match_title(page_text)

            if is_bookmyshow_url(url):
                keywords_live = BMS_KEYWORDS_LIVE
                keywords_waiting = BMS_KEYWORDS_WAITING
                platform = "BookMyShow"
            else:
                keywords_live = DISTRICT_KEYWORDS_LIVE
                keywords_waiting = DISTRICT_KEYWORDS_WAITING
                platform = "District by Zomato"

            is_live = any(kw in page_text_lower for kw in keywords_live)
            is_waiting = any(kw in page_text_lower for kw in keywords_waiting)

            if is_live and not is_waiting:
                status = "🟢 *LIVE — Book now!*"
            elif is_waiting:
                status = "🟡 *Coming soon*"
            else:
                status = "🔴 *Not open yet*"

            send_telegram(
                f"{status}\n\n"
                f"🏏 *{match_title}*\n"
                f"🎫 {platform}\n"
                f"🔗 {url}"
            )

        except Exception as e:
            send_telegram(f"⚠️ Could not check:\n`{url}`\nError: {str(e)[:100]}")


def process_updates():
    offset = load_offset()
    updates = get_updates(offset)

    if not updates:
        print("No new Telegram messages.")
        return False

    urls = load_urls()
    changed = False

    for update in updates:
        update_id = update["update_id"]
        save_offset(update_id + 1)

        message = update.get("message", {})
        chat_id = str(message.get("chat", {}).get("id", ""))
        text = message.get("text", "").strip()

        if chat_id != TELEGRAM_CHAT_ID:
            print(f"Ignoring message from unknown chat: {chat_id}")
            continue

        print(f"Received message: {text}")

        if is_valid_url(text):
            # Direct URL — add immediately
            if text not in urls:
                urls.append(text)
                changed = True
                platform = "BookMyShow" if is_bookmyshow_url(text) else "District by Zomato"
                send_telegram(
                    f"✅ *URL added!* I'll start checking this match.\n\n"
                    f"🎫 Platform: {platform}\n"
                    f"`{text}`\n\n"
                    f"You'll get an alert when tickets go live 🎟️"
                )
            else:
                send_telegram(f"ℹ️ Already tracking this URL:\n`{text}`")

        elif text.lower() == "/status":
            run_status_check(urls)

        elif text.lower() == "/list":
            if urls:
                url_list = "\n".join([f"• `{u}`" for u in urls])
                send_telegram(f"📋 *Currently tracking {len(urls)} URL(s):*\n\n{url_list}")
            else:
                send_telegram("📋 No URLs being tracked yet.")

        elif text.lower() == "/clear":
            urls = []
            changed = True
            send_telegram("🗑️ All URLs cleared.")

        elif text.lower().startswith("/remove"):
            parts = text.split(" ", 1)
            if len(parts) > 1:
                to_remove = parts[1].strip()
                if to_remove in urls:
                    urls.remove(to_remove)
                    changed = True
                    send_telegram(f"🗑️ Removed:\n`{to_remove}`")
                else:
                    send_telegram("⚠️ URL not found in tracking list.")
            else:
                send_telegram("Usage: `/remove <url>`")

        elif text.lower().startswith("/"):
            # Unknown command
            send_telegram(
                "👋 *IPL Ticket Bot*\n\n"
                "*Commands:*\n"
                "• `/status` — check all tracked matches right now\n"
                "• `/list` — see all tracked URLs\n"
                "• `/remove <url>` — stop tracking a URL\n"
                "• `/clear` — remove all URLs\n\n"
                "Or just describe a match (e.g. _DC vs RCB 27th April_) and I'll find and track it!"
            )

        else:
            # Natural language query — try to find match on District
            send_telegram(f"🔍 Searching for *{text}* on District by Zomato...")
            match, candidates = find_match_from_query(text)

            if match:
                title, url = match
                if url not in urls:
                    urls.append(url)
                    changed = True
                    send_telegram(
                        f"✅ *Found and added!*\n\n"
                        f"🏏 *{title}*\n\n"
                        f"🔗 `{url}`\n\n"
                        f"You'll get an alert when tickets go live 🎟️"
                    )
                else:
                    send_telegram(
                        f"ℹ️ Already tracking this match:\n\n"
                        f"🏏 *{title}*"
                    )
            elif candidates:
                candidate_list = "\n".join([f"• {t}" for t, u in candidates])
                send_telegram(
                    f"🤔 Found a few possible matches — can you be more specific?\n\n"
                    f"{candidate_list}\n\n"
                    f"Try adding the date or full team names, or send the URL directly from:\n"
                    f"{IPL_BOOKING_URL_DISTRICT}"
                )
            else:
                send_telegram(
                    f"😕 Couldn't find a match for *{text}* on District.\n\n"
                    f"Try sending the URL directly from:\n"
                    f"{IPL_BOOKING_URL_DISTRICT}"
                )

    if changed:
        save_urls(urls)
        print(f"urls.txt updated with {len(urls)} URL(s).")

    return changed


if __name__ == "__main__":
    process_updates()

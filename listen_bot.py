import os
import requests
from bs4 import BeautifulSoup

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
URLS_FILE = "urls.txt"
OFFSET_FILE = ".last_update_id"

KEYWORDS_LIVE = ["sale is live", "pre-sale is live", "book now", "buy tickets"]
KEYWORDS_WAITING = ["tickets available in", "coming soon"]
KEYWORDS_NOT_OPEN_YET = ["be the first to know when sale begins"]

IPL_BOOKING_URL = "https://www.district.in/events/ipl-ticket-booking"


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


def get_match_title(page_text):
    for line in page_text.splitlines():
        line = line.strip()
        if line:
            return line[:100]
    return "Unknown Match"


def run_status_check(urls):
    """Immediately check all tracked URLs and report status to Telegram."""
    if not urls:
        send_telegram("📋 No URLs being tracked yet. Send a district.in URL to add one!")
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

            is_live = any(kw in page_text_lower for kw in KEYWORDS_LIVE)
            is_waiting = any(kw in page_text_lower for kw in KEYWORDS_WAITING)
            is_not_open_yet = any(kw in page_text_lower for kw in KEYWORDS_NOT_OPEN_YET)

            if is_live and not is_waiting:
                status = "🟢 *LIVE — Book now!*"
            elif is_waiting:
                status = "🟡 *Coming soon*"
            elif is_not_open_yet:
                status = "🔴 *Not open yet*"
            else:
                status = "🔴 *Not open yet*"

            send_telegram(
                f"{status}\n\n"
                f"🏏 *{match_title}*\n"
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

        if text.startswith("https://www.district.in") or text.startswith("https://district.in"):
            if text not in urls:
                urls.append(text)
                changed = True
                send_telegram(
                    f"✅ *URL added!* I'll start checking this match for ticket availability.\n\n"
                    f"`{text}`\n\n"
                    f"You'll get an alert when tickets go live 🎟️"
                )
                print(f"Added URL: {text}")
            else:
                send_telegram(f"ℹ️ Already tracking this URL:\n`{text}`")

        elif text.lower() == "/status":
            run_status_check(urls)

        elif text.lower() == "/list":
            if urls:
                url_list = "\n".join([f"• `{u}`" for u in urls])
                send_telegram(f"📋 *Currently tracking {len(urls)} URL(s):*\n\n{url_list}")
            else:
                send_telegram("📋 No URLs being tracked yet. Send me a district.in URL to add one!")

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

        else:
            send_telegram(
                "👋 *IPL Ticket Bot*\n\n"
                "Send me a `district.in` match URL and I'll track it for you!\n\n"
                "*Commands:*\n"
                "• `/status` — check all tracked matches right now\n"
                "• `/list` — see all tracked URLs\n"
                "• `/remove <url>` — stop tracking a URL\n"
                "• `/clear` — remove all URLs"
            )

    if changed:
        save_urls(urls)
        print(f"urls.txt updated with {len(urls)} URL(s).")

    return changed


if __name__ == "__main__":
    process_updates()

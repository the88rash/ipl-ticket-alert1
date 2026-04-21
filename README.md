# 🏏 IPL Ticket Alert Bot

[![Use this template](https://img.shields.io/badge/Use%20this%20template-2ea44f?style=for-the-badge&logo=github)](https://github.com/the88rash/ipl-ticket-alert1/generate)
[![GitHub Actions](https://img.shields.io/badge/Powered%20by-GitHub%20Actions-blue?style=for-the-badge&logo=githubactions)](https://github.com/features/actions)
[![Telegram](https://img.shields.io/badge/Alerts%20via-Telegram-26A5E4?style=for-the-badge&logo=telegram)](https://telegram.org)

Automatically checks ticket availability for **any IPL 2026 match** across **District by Zomato**, **BookMyShow**, and the **RCB Official Website** — and sends you a **Telegram alert** the moment tickets go live.

Runs entirely on **GitHub Actions** — no server or laptop needed.

---

## ✨ Features

- 🔔 **Real-time alerts** via Telegram when tickets go live or are coming soon
- 🏟️ **Supports all 3 platforms** — District by Zomato, BookMyShow, RCB website
- 💬 **Natural language match search** — just type "DC vs RCB 27th April" and the bot finds and tracks it
- 📋 **Bot commands** to manage your tracked matches anytime
- ⏱️ **Checks every 15 minutes** automatically via GitHub Actions

---

## ⚙️ Setup (10 minutes)

### Step 1 — Create your Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send `/newbot` and follow the prompts
3. Copy the **Bot Token** (looks like `123456:ABCdef...`)
4. Search for **@userinfobot**, send any message, copy your **Chat ID**
5. Open your new bot on Telegram and press **Start**

---

### Step 2 — Create the GitHub repo

1. Go to [github.com](https://github.com) and create a free account
2. Create a new repository (e.g. `ipl-ticket-alert`)
3. Upload all files maintaining this structure:

```
your-repo/
├── .github/
│   └── workflows/
│       └── check_tickets.yml
├── check_tickets.py
├── listen_bot.py
├── matches.json
└── urls.txt
```

---

### Step 3 — Add your secrets to GitHub

Go to **Settings → Secrets and variables → Actions → New repository secret** and add:

| Secret Name | Value |
|---|---|
| `TELEGRAM_TOKEN` | Your BotFather token |
| `TELEGRAM_CHAT_ID` | Your Chat ID from @userinfobot |

---

### Step 4 — Grant workflow write permissions

Go to **Settings → Actions → General → Workflow permissions** → select **"Read and write permissions"** → Save.

This allows the bot to save new URLs you send it back to the repo.

---

### Step 5 — Enable GitHub Actions

1. Go to the **Actions** tab in your repo
2. Click **"I understand my workflows, go ahead and enable them"**
3. Click **IPL Ticket Checker → "Run workflow"** to test manually first

---

## 💬 Bot Commands

Interact with your bot directly from Telegram:

| Command / Message | What it does |
|---|---|
| Send a `district.in` or `bookmyshow.com` URL | Adds that match to tracking |
| Send `https://shop.royalchallengers.com/ticket\|RCB vs GT\|24 Apr 2026` | Adds an RCB match to tracking |
| Describe a match (e.g. _DC vs RCB 27th April_) | Bot finds and tracks it automatically |
| `/status` | Immediately checks all tracked matches and reports status |
| `/list` | Shows all currently tracked URLs |
| `/remove <url>` | Stops tracking a specific match |
| `/clear` | Removes all tracked matches |

---

## 🏟️ Supported Platforms

| Platform | Home Teams | How to track |
|---|---|---|
| **District by Zomato** | DC, CSK, SRH, RR, PBKS | Send match URL or describe match |
| **BookMyShow** | GT, KKR, LSG, MI | Send match URL or describe match |
| **RCB Official Website** | RCB | Send in pipe format (see below) or describe match |

### Adding an RCB match

RCB uses a single page for all matches. Send this format to your bot:
```
https://shop.royalchallengers.com/ticket|RCB vs GT|24 Apr 2026
```
Or just describe it naturally: _"RCB vs Gujarat 24th April"_ — the bot will find it and format it correctly.

---

## 📱 What the Telegram alerts look like

**When tickets go LIVE:**
```
🚨 YOUR PREFERRED IPL TICKETS ARE LIVE! 🚨

🏏 Match 39 - Delhi Capitals vs Royal Challengers Bengaluru
🎫 Platform: District by Zomato

👉 Book NOW before they sell out:
https://www.district.in/events/tata-ipl-2026-match-39...

🎟️ All IPL matches:
https://www.district.in/events/ipl-ticket-booking

⚡ You have only 10 mins once you select seats!
```

**When tickets are coming soon:**
```
🚨 YOUR PREFERRED IPL TICKETS ARE COMING SOON! 🚨

🏏 Match 39 - Delhi Capitals vs Royal Challengers Bengaluru
🎫 Platform: District by Zomato

👉 SET A REMINDER ON PHONE:
https://www.district.in/events/tata-ipl-2026-match-39...
```

**When you run /status:**
```
🟢 LIVE — Book now!

🏏 Book tickets to TATA IPL 2026: Match 39
🎫 District by Zomato
🔗 https://www.district.in/...
```

---

## 📁 File Overview

| File | Purpose |
|---|---|
| `check_tickets.py` | Fetches match pages and checks ticket status, sends alerts |
| `listen_bot.py` | Polls Telegram for your messages, updates `urls.txt` |
| `matches.json` | Pre-loaded list of all 41 remaining IPL 2026 matches with URLs |
| `urls.txt` | Your personal list of matches being tracked |
| `.github/workflows/check_tickets.yml` | GitHub Actions workflow — runs every 15 minutes |

---

## ⚠️ Notes

- **GitHub Actions free tier** gives 2,000 minutes/month — at 15-minute intervals this uses ~100 mins/week, well within limits
- **BookMyShow and RCB** may block automated requests (403 error) — the bot will notify you to check manually if this happens
- Bot commands take up to **15 minutes** to respond since they're picked up on the next scheduled run. For instant response, trigger the workflow manually from the Actions tab
- The `matches.json` covers all **41 remaining IPL 2026 league matches** (matches 30–70)
- Disable the workflow anytime from the **Actions tab** once the season ends

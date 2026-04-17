# 🏏 IPL Ticket Alert — DC vs RCB (April 27)

Automatically checks District.in every 5 minutes and sends a **Telegram alert** the moment tickets go live for DC vs RCB on April 27 at Arun Jaitley Stadium.

---

## ⚙️ Setup (10 minutes)

### Step 1 — Create your Telegram Bot
1. Open Telegram and search for **@BotFather**
2. Send `/newbot` and follow the prompts
3. Copy the **Bot Token** (looks like `123456:ABCdef...`)
4. Search for **@userinfobot**, send any message, copy your **Chat ID**

---

### Step 2 — Fork or create this repo on GitHub
1. Go to [github.com](https://github.com) and create a free account
2. Create a new repository named `ipl-ticket-alert`
3. Upload both files:
   - `check_tickets.py`
   - `.github/workflows/check_tickets.yml`

---

### Step 3 — Add your secrets to GitHub
1. In your repo, go to **Settings → Secrets and variables → Actions**
2. Click **"New repository secret"** and add:

| Secret Name | Value |
|---|---|
| `TELEGRAM_TOKEN` | Your BotFather token |
| `TELEGRAM_CHAT_ID` | Your Chat ID from @userinfobot |

---

### Step 4 — Enable GitHub Actions
1. Go to the **Actions** tab in your repo
2. Click **"I understand my workflows, go ahead and enable them"**
3. Click on **IPL Ticket Checker** → **"Run workflow"** to test it manually first

---

## ✅ How to verify it's working
- Click **Actions** tab → you should see runs every 5 minutes
- Each run will show ✅ green if it checked successfully
- You'll get a Telegram message the moment tickets go live!

---

## 📱 What the Telegram alert looks like

```
🚨 IPL TICKETS ARE LIVE! 🚨

🏏 DC vs RCB — April 27, 7:30 PM
📍 Arun Jaitley Stadium, Delhi

👉 Book NOW before they sell out:
https://www.district.in/events/delhi-capitals-team

⚡ You have only 10 mins once you select seats!
```

---

## ⚠️ Notes
- GitHub Actions free tier gives 2,000 minutes/month — this workflow uses ~400 mins total until April 27, well within limits
- The workflow auto-stops after April 27 (you can disable it manually from the Actions tab anytime)

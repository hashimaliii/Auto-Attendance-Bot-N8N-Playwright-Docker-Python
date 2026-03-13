# Auto-Attendance-Bot — Setup Guide

An automated attendance bot that listens for Google Meet links via WhatsApp (groups or DMs) and Google Classroom email notifications. Once a link is detected, it opens a browser, turns off the mic and camera, and joins the class on your behalf. After joining, it sends you a WhatsApp confirmation message.

---

## How It Works

```
WhatsApp Message ──► n8n Webhook ──► Fetch Settings ──► Merge ──► Code ──► IsAllowed? ──► Join ──► Notify
                                                                     ▲
Gmail (IMAP) ────► n8n Email Trigger ──► Fetch Settings ──► Update IMAP Creds ──► Pass Settings ──► Merge ──┘
```

- **WhatsApp trigger:** Any Meet link sent to a group or DM where the bot is present is auto-joined immediately — no class name check.
- **Email trigger:** Only joins if the email contains a Meet URL and the class name matches your allowed list (leave the list empty to allow all classes).

---

## Prerequisites

- Windows PC (the `.bat` launcher handles everything else)
- Docker Desktop installed (the launcher will install it if missing)
- A secondary/personal Gmail account (used as the email bridge)
- A WhatsApp account (used to trigger the bot and receive confirmations)

---

## File Structure

```
project/
├── local-browser-bridge/
│   └── docker-compose.yml       ← Runs n8n + Evolution API (WhatsApp)
├── python-bot/
│   ├── app.py                   ← Flask server + Playwright browser bot
│   ├── config.json              ← Your settings (auto-created on first run)
│   └── templates/
│       └── index.html           ← Web control panel (http://localhost:5000)
├── attendance_workflow.json     ← n8n workflow to import
└── start_bot.bat                ← Double-click to start everything
```

---

## Step 1: Start Everything

Run the launcher for your operating system:

**Windows** — Double-click **`start_bot.bat`**

**Linux / macOS** — Open a terminal in the project folder and run:
```bash
chmod +x start_bot.sh
./start_bot.sh
```

Both launchers automatically:
1. Install Docker if not found (Windows asks for a reboot, Linux asks you to log out and back in)
2. Start n8n (`http://localhost:5678`) and Evolution API (`http://localhost:8080`)
3. Create a Python virtual environment, install Flask and Playwright
4. Open the control panel at `http://localhost:5000`
5. Start the Python bot server

> ⚠️ **Do not close the terminal window** while you want the bot to be active.

---

## Step 2: Import the n8n Workflow

1. Open **`http://localhost:5678`** and create an account if prompted.
2. Go to **Workflows** → **Import from File**.
3. Select `attendance_workflow.json`.
4. Click **Save** then **Activate** (toggle in top-right).

---

## Step 3: Connect Your WhatsApp

**1. Create the Bot Instance**

Run this in your terminal (or PowerShell):

```bash
curl -X POST "http://localhost:8080/instance/create" \
  -H "apikey: hashim_secret_key" \
  -H "Content-Type: application/json" \
  -d "{\"instanceName\": \"ClassBot\", \"qrcode\": true, \"webhook_url\": \"http://host.docker.internal:5678/webhook/whatsapp\", \"webhook_by_events\": false, \"webhook_events\": [\"MESSAGES_UPSERT\"]}"
```

**2. Scan the QR Code**

The response will contain a QR code. On your phone:
> **WhatsApp → Linked Devices → Link a Device → Scan QR**

**3. Enable Group Messages**

```bash
curl -X POST "http://localhost:8080/settings/set/ClassBot" \
  -H "apikey: hashim_secret_key" \
  -H "Content-Type: application/json" \
  -d "{\"reject_call\": false, \"groups_ignore\": false, \"always_online\": true, \"read_messages\": false, \"read_status\": false, \"sync_full_history\": false}"
```

---

## Step 4: Configure the Settings (Control Panel)

Open **`http://localhost:5000`** in your browser. Fill in all fields and click **Save & Apply Settings**.

| Field | What to Enter |
|---|---|
| **Phone Number** | Your WhatsApp number — country code, no `+`. Example: `923123456789` |
| **Allowed Class Names** | Comma-separated class names in lowercase. Example: `devops a a, scd lab fall 2025`. Leave **empty** to join all classes. |
| **Bridge Gmail Address** | Your personal Gmail (e.g. `you@gmail.com`) |
| **Gmail App Password** | 16-character app password from Google (see below) |
| **n8n API Key** | Get it from n8n → **Settings** (bottom-left) → **n8n API** → **Create an API key** |

### Getting a Gmail App Password
1. Go to [myaccount.google.com/security](https://myaccount.google.com/security)
2. Enable **2-Step Verification** if not already on
3. Search for **"App passwords"** → Create one → Select **Mail** → Copy the 16-character key

---

## Step 5: Set Up the Email Bridge

The bot reads emails from your personal Gmail to catch Google Classroom announcements.

**In your university `.edu` email:**
1. Go to **Settings → Forwarding**
2. Add a forwarding address: your personal Gmail
3. Create a filter:
   - **From:** `no-reply@classroom.google.com`
   - **Action:** Forward to your personal Gmail

**That's it.** The n8n workflow automatically updates the IMAP credentials using the values from your control panel — no manual setup in n8n is needed.

---

## Step 6: Log In to Google (First Time Only)

The bot uses a persistent browser profile so it only needs to log in once.

1. The first time `app.py` runs, a Chromium window will open.
2. Manually navigate to [meet.google.com](https://meet.google.com) and sign in with your Google account.
3. Close the browser.
4. From now on the bot will use the saved session automatically.

> The session is stored in `python-bot/browser_profile/`. If the bot ever gets logged out, just delete that folder and log in again.

---

## Testing the Bot

| Trigger | How to Test |
|---|---|
| **WhatsApp** | Send a Google Meet link in any group or DM where the bot's WhatsApp is present. The bot joins automatically and sends you a confirmation. |
| **Email** | Forward an old Google Classroom email to your bridge Gmail and mark it as **Unread**. The bot will pick it up on the next poll. |

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Bot joins but camera is still on | Make sure `app.py` is the latest version. The bot clicks the camera off button on the pre-join screen before joining. |
| `isAllowed: false` for a class you added | Make sure the class name in the allowed list exactly matches the text in the email, all lowercase. The bot strips HTML and searches the full email body. |
| WhatsApp confirmation not sending | Check that your phone number in the control panel has no `+` sign and no spaces. |
| n8n workflow shows `UpdateIMAPCredential` error | Make sure you saved a valid n8n API key in the control panel (no extra spaces). Get it from n8n → Settings (bottom-left) → n8n API. |
| Bot stopped logging in to Google | Delete `python-bot/browser_profile/` and log in to Google manually again in the Chromium window. |
| Docker not starting | Run `start_bot.bat` as Administrator, or open Docker Desktop manually and wait for it to fully start. |

---

## Disclaimer

This tool is for educational and personal productivity purposes only. Use responsibly and ensure compliance with your institution's attendance policies.
# Auto-Attendance-Bot-N8N-Node-Docker-Python

An automated attendance bot that listens for Google Meet links via WhatsApp (Groups or Direct Messages) and Google Classroom email notifications. Once a link is detected, it triggers a local Python script using Playwright to automatically open a browser, mute the microphone and camera, and join the class on your behalf.

---

## Features

- **Multi-Trigger System:** Detects Google Meet links via WhatsApp messages or Google Classroom email announcements.
- **Smart Routing:** Auto-replies to the exact WhatsApp group or private chat that sent the link.
- **Classroom Filtering:** Only joins classes that match a predefined "Allowed List" (ignores random links).
- **Bypass IT Blocks:** Uses an email forwarding bridge to bypass strict University IMAP restrictions.
- **Auto-Mute & Join:** Uses Playwright to handle the browser UI, skip login screens (via persistent sessions), mute audio/video, and click the "Join" button automatically.
- **Non-Blocking Architecture:** Python uses threading to instantly notify n8n of success while staying in the meeting for the duration of the class.

---

## Prerequisites

- **Docker & Docker Compose** (for running n8n and Evolution API)
- **Python 3.10+**
- A secondary/personal Gmail account (to act as an email bridge)
- A WhatsApp account (to act as the trigger and sender)

---

## Setup Guide

### Step 1: Spin Up n8n and Evolution API

Navigate to the local infrastructure folder and start the Docker containers. This will boot up your automation engine (n8n) and your WhatsApp API (Evolution).

```bash
cd local-browser-bridge
docker-compose up -d
```

| Service | URL |
|---|---|
| n8n | `http://localhost:5678` |
| Evolution API | `http://localhost:8080` |

---

### Step 2: Connect Your WhatsApp & Set the Webhook

You need to link your personal WhatsApp to Evolution API and tell it to forward incoming messages to n8n.

**1. Get your n8n Webhook URL**

Open n8n, double-click the very first **Webhook** node, and copy the Production URL. It will look like:
```
http://n8n:5678/webhook/whatsapp
```
or
```
http://YOUR_IP:5678/webhook/whatsapp
```

**2. Create the Bot Instance & Set the Webhook**

Run this command in your terminal to create the instance and configure the webhook simultaneously. Replace `YOUR_SECRET_KEY` and the `url` value if necessary:

```bash
curl -X POST "http://localhost:8080/instance/create" -H "apikey: YOUR_SECRET_KEY" -H "Content-Type: application/json" -d '{"instanceName": "ClassBot", "qrcode": true, "webhook_url": "http://host.docker.internal:5678/webhook/whatsapp", "webhook_by_events": false, "webhook_events": ["MESSAGES_UPSERT"]}'
```

**3. Scan the QR Code**

The API will return a base64 image or a terminal QR code. On your phone:

> **WhatsApp** → **Linked Devices** → **Link a Device** → Scan the QR code

**4. Enable Group Messages**

By default, Evolution API ignores group chats. Run this command to force it to listen to your university groups:

```bash
curl -X POST "http://localhost:8080/settings/set/ClassBot" \
  -H "apikey: YOUR_SECRET_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "reject_call": false,
    "groups_ignore": false,
    "always_online": true,
    "read_messages": false,
    "read_status": false,
    "sync_full_history": false
  }'
```

---

### Step 3: Set Up the Python Playwright Bot

This script controls the actual browser interactions.

**1. Navigate to the Python bot directory:**

```bash
cd python-bot
```

**2. Set up your virtual environment and install dependencies:**

```bash
python -m venv venv

# On Windows:
venv\Scripts\activate

# On Mac/Linux:
source venv/bin/activate

pip install flask playwright
playwright install chromium
```

**3. Run the Flask server:**

```bash
python app.py
```

> **Note:** The first time it runs, you may need to manually log in to Google. The session will be saved in the `browser_profile` folder for automatic logins going forward.

---

### Step 4: Import the n8n Workflow

1. Open n8n at `http://localhost:5678`.
2. Go to **Workflows** → **Import from File**.
3. Select the `attendance workflow.json` file from this repository.
4. Open the **HTTP Request1** node (the WhatsApp confirmation node) and ensure the URL points to your Evolution API container:
   ```
   http://host.docker.internal:8080/message/sendText/ClassBot
   ```
5. Verify your API Key is correctly set in the request Header.

---

### Step 5: Configure the Google Classroom Email Bridge

To bypass university IT restrictions on IMAP, use a personal Gmail account to catch forwarded notifications.

1. Create an **App Password** in your personal Google Account under **Security Settings**.
2. In n8n, open the **Email Trigger (IMAP)** node and enter your personal email credentials and App Password. Set it to only fetch `["UNSEEN"]` emails.
3. In your University `.edu` email settings, create an auto-forwarding rule:
   > Forward all emails from `no-reply@classroom.google.com` → your personal Gmail address.

---

### Step 6: Customize Your Allowed Classes

Open the **Code in JavaScript** node in n8n and update the `allowedClasses` array with the exact names of the classes you want to attend.

> **All class names must be written in lowercase.**

```javascript
const allowedClasses = [
  "devops a a",
  "scd lab fall 2025",
  "software engineering"
];
```

---

### Step 7: Set Your WhatsApp Number for Confirmations

Because WhatsApp Web/Desktop sometimes sends a linked device ID (`@lid`) instead of a real phone number, you need to hardcode your phone number so the bot always knows where to send private confirmation messages.

1. In n8n, open the **HTTP Request1** node (the final node that sends the WhatsApp message).
2. In the **Body** section, replace `923XXXXXXXXX` with your actual number — no plus sign, no spaces.

```json
{
  "number": "{{ $('Webhook').item.json.body.data.key.remoteJid.includes('@g.us') ? $('Webhook').item.json.body.data.key.remoteJid : '923XXXXXXXXX@s.whatsapp.net' }}",
  "textMessage": {
    "text": "Bot Status: I have successfully joined the class!"
  }
}
```

> **How smart routing works:** If the Meet link came from a group chat, the bot replies to that group. If it came from a private chat or an email trigger, it sends the confirmation directly to your hardcoded number.

---

## Testing the Flow

| Trigger | How to Test |
|---|---|
| **WhatsApp** | Send a Google Meet link in a group or DM where the bot is present. n8n catches it → Python opens the browser → you receive a WhatsApp confirmation. |
| **Email** | Forward an old Google Classroom email to your bridge Gmail address and mark it as **Unread**. n8n will pick it up on the next poll cycle. |

---

## Disclaimer

This tool is for educational purposes only. Use responsibly and ensure compliance with your institution's attendance policies.
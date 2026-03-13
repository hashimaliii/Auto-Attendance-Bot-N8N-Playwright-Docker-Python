# How to Restart the Bot After a Reboot

When you restart your computer, all background processes (Docker, n8n, Evolution API, and the Python server) will stop. Use this checklist to get the Auto-Attendance Bot back online in under 2 minutes.

---

### Step 1: Start Docker

Make sure the Docker daemon is running before issuing any commands.

- **Windows / Mac:** Open the **Docker Desktop** application and wait for the engine status to show "Running".
- **Linux:** Docker usually starts on boot. Verify with:
  ```bash
  sudo systemctl status docker
  ```

---

### Step 2: Spin Up the Infrastructure (n8n & Evolution API)

Open a terminal, navigate to the local infrastructure folder, and start the containers in the background.

```bash
cd local-browser-bridge
docker-compose up -d
```

Wait a few seconds for the containers to fully boot before moving on.

---

### Step 3: Start the Python Playwright Bot

Open a new terminal window and start the Flask server that controls the browser.

```bash
cd python-bot

# Activate your virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Start the server
python app.py
```

> **Keep this terminal window open.** Closing it takes the Python bot offline.

---

### Step 4: Verify Everything is Working

You do not need to re-scan the WhatsApp QR code or re-enter any passwords — everything is saved in your local volumes and browser profiles.

To confirm the bot is ready:

1. Open `http://localhost:5678` and verify that n8n is running and your workflow is set to **Active**.
2. Drop a dummy `https://meet.google.com/xxx-xxxx-xxx` link into your WhatsApp chat, or forward an old email to your bridge address.
3. Watch the Python terminal — the browser should boot up and join the meeting automatically.

---

## Tip: Skip Step 2 on Every Reboot

If your `docker-compose.yml` has `restart: unless-stopped` set on each service, Docker will start n8n and Evolution API automatically on boot. After enabling that, the only manual step after a restart is running the Python server.
from flask import Flask, request, jsonify, render_template
from playwright.sync_api import sync_playwright
import os
import threading
import json
import time

app = Flask(__name__)

# --- CONFIGURATION MANAGEMENT ---
CONFIG_FILE = os.path.join(os.getcwd(), "config.json")
USER_DATA_DIR = os.path.join(os.getcwd(), "browser_profile")

def load_config():
    if not os.path.exists(CONFIG_FILE):
        default_config = {
            "whatsapp_number": "",
            "allowed_classes": "devops, scd lab",
            "bridge_email": "",
            "bridge_password": "",
            "success_message": "✅ Bot Status: I have successfully joined the class! 🎓"
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(default_config, f, indent=4)
        return default_config
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

# --- ROUTES ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/config', methods=['GET', 'POST'])
def handle_config():
    if request.method == 'POST':
        data = request.json
        with open(CONFIG_FILE, 'w') as f:
            json.dump(data, f, indent=4)
        return jsonify({"status": "saved"})
    return jsonify(load_config())

@app.route('/api/n8n_settings', methods=['GET'])
def n8n_settings():
    # n8n uses this to get your phone/classes/email creds dynamically
    return jsonify(load_config())

@app.route('/join', methods=['GET'])
def join_meeting():
    meet_url = request.args.get('url')
    if not meet_url:
        return jsonify({"error": "No URL provided"}), 400
    
    # Run browser in a background thread so n8n isn't kept waiting
    threading.Thread(target=run_browser_logic, args=(meet_url,)).start()
    return jsonify({"status": "Launching browser", "url": meet_url})

# --- BROWSER LOGIC ---
def run_browser_logic(url):
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=False, # Set to True once you've logged into Google once
            args=["--use-fake-ui-for-media-stream"] # Bypasses mic/cam prompts
        )
        page = browser.new_page()
        print(f"[*] Navigating to: {url}")
        page.goto(url)
        
        # Give time for initial load
        time.sleep(5)
        
        try:
            # Step 1: Dismiss "Receive notifications" popup
            try:
                not_now = page.get_by_role("button", name="Not now")
                not_now.wait_for(state="visible", timeout=5000)
                not_now.click()
                print("[V] Dismissed notification popup.")
                time.sleep(1)
            except Exception:
                pass

            # Step 2: Dismiss any other overlay via Escape
            page.keyboard.press("Escape")
            time.sleep(1)

            # Step 3: Turn off camera using the PRE-JOIN screen toggle button
            # These are the actual aria-labels on the pre-join screen
            cam_selectors = [
                '[data-tooltip="Turn off camera"]',
                '[aria-label="Turn off camera"]',
                '[aria-label="Turn off camera (Ctrl+E)"]',
                'div[data-is-muted="false"][data-tooltip*="camera"]',
            ]
            cam_turned_off = False
            for sel in cam_selectors:
                try:
                    btn = page.locator(sel).first
                    if btn.is_visible(timeout=2000):
                        btn.click()
                        print("[V] Camera turned off via pre-join button.")
                        cam_turned_off = True
                        time.sleep(1)
                        break
                except Exception:
                    continue

            # Step 4: Also try keyboard shortcut as backup
            if not cam_turned_off:
                page.keyboard.down("Control")
                page.keyboard.press("e")
                page.keyboard.up("Control")
                print("[V] Camera toggle attempted via Ctrl+E.")
                time.sleep(1)

            # Step 5: Mute mic
            try:
                mic_selectors = [
                    '[data-tooltip="Turn off microphone"]',
                    '[aria-label="Turn off microphone"]',
                    '[aria-label="Turn off microphone (Ctrl+D)"]',
                ]
                for sel in mic_selectors:
                    btn = page.locator(sel).first
                    if btn.is_visible(timeout=2000):
                        btn.click()
                        print("[V] Mic turned off via pre-join button.")
                        time.sleep(1)
                        break
            except Exception:
                page.keyboard.down("Control")
                page.keyboard.press("d")
                page.keyboard.up("Control")
                print("[V] Mic toggle attempted via Ctrl+D.")
                time.sleep(1)

            # Step 6: Dismiss "Camera not found" popup if it appeared
            try:
                close_btn = page.locator('[aria-label="Close dialog"]').first
                if close_btn.is_visible(timeout=2000):
                    close_btn.click()
                    print("[V] Dismissed Camera not found dialog.")
            except Exception:
                pass
            try:
                # The X button on the camera popup
                page.locator('xpath=//div[@role="alertdialog"]//button').first.click()
                time.sleep(0.5)
            except Exception:
                pass

            # Step 7: Click Join now
            join_locators = [
                page.get_by_role("button", name="Join now"),
                page.get_by_role("button", name="Ask to join"),
                page.get_by_role("button", name="Join now without camera"),
                page.locator('button[jsname="Qx7uuf"]').first,
            ]

            joined = False
            for locator in join_locators:
                try:
                    if locator.is_visible(timeout=3000):
                        locator.click()
                        print("[V] Clicked Join Button.")
                        joined = True
                        break
                except Exception:
                    continue

            if not joined:
                print("[!] Could not find Join button.")
            
            # Stay in meeting for 1 hour (3600 seconds)
            time.sleep(3600)
            
        except Exception as e:
            print(f"[!] Error during automation: {e}")
        finally:
            browser.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
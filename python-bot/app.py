from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright
import os

app = Flask(__name__)

# This folder keeps you logged in so you don't have to enter the password every time
USER_DATA_DIR = os.path.join(os.getcwd(), "browser_profile")

@app.route('/join', methods=['POST'])
def join_meeting():
    data = request.json
    meeting_url = data.get('url')

    if not meeting_url:
        return jsonify({"error": "No meeting URL provided"}), 400

    print(f"Booting up browser for: {meeting_url}")

    with sync_playwright() as p:
        # Launching with the persistent context (your "saved" session)
        browser_context = p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=False,
            viewport={'width': 1280, 'height': 720},
            permissions=['camera', 'microphone'],
            args=[
                "--disable-blink-features=AutomationControlled",
                "--use-fake-ui-for-media-stream", 
                "--use-fake-device-for-media-stream"
            ] 
        )
        
        page = browser_context.pages[0]
        page.goto(meeting_url)
        
        # --- 1. THE PASSWORD AUTO-LOGIN ---
        try:
            # Check if password field exists
            print("Checking if login is required...")
            password_input = page.locator('input[type="password"]').first
            password_input.wait_for(state="visible", timeout=5000)
            
            print("Password screen detected. Entering password...")
            password_input.fill("#Possible1")
            page.keyboard.press("Enter")
            
            # Wait for the meeting page to load after login
            page.wait_for_load_state("networkidle")
            print("Login successful.")
        except Exception:
            print("No password screen detected. Proceeding...")

        print("Waiting 5 seconds for meeting UI to settle...")
        page.wait_for_timeout(5000) 

        # --- 2. DUAL-METHOD MICROPHONE MUTE ---
        print("Attempting to mute Microphone...")
        try:
            mic_button = page.locator('[aria-label*="microphone" i]').first
            mic_button.click(timeout=3000)
            print("Success: Clicked Microphone via DOM label.")
        except Exception:
            print("DOM locator failed. Falling back to coordinates...")
            page.mouse.click(420, 660) # Fallback coordinates
            
        page.wait_for_timeout(1000)

        # --- 3. DUAL-METHOD CAMERA MUTE ---
        print("Attempting to turn off Camera...")
        try:
            cam_button = page.locator('[aria-label*="camera" i]').first
            cam_button.click(timeout=3000)
            print("Success: Clicked Camera via DOM label.")
        except Exception:
            print("DOM locator failed. Falling back to coordinates...")
            page.mouse.click(480, 660) # Fallback coordinates

        page.wait_for_timeout(1000)

        # --- 4. DUAL-METHOD JOIN BUTTON ---
        print("Looking for the join button...")
        join_texts = ["Join now", "Ask to join", "Switch here", "Join"]
        joined = False
        
        for text in join_texts:
            try:
                locator = page.get_by_text(text, exact=True).first
                if locator.is_visible(timeout=2000):
                    locator.click()
                    print(f"Success: Clicked '{text}' via text locator.")
                    joined = True
                    break
            except Exception:
                continue
        
        if not joined:
            print("Text locator failed. Falling back to Join button coordinates...")
            page.mouse.click(900, 450) # Fallback coordinates
            print("Clicked Join area via coordinates.")

        # Keep browser open for 1 hour (3600000 ms)
        print("Bot is in. Standing by for 1 hour...")
        page.wait_for_timeout(3600000) 
        
        browser_context.close()

    return jsonify({"status": "success", "message": "Attended meeting!"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
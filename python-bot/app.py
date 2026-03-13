from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright
import os
import threading
import time

app = Flask(__name__)

# This folder keeps you logged in (saves your cookies/session)
USER_DATA_DIR = os.path.join(os.getcwd(), "browser_profile")

def run_browser_logic(meeting_url):
    """This function runs in the background so it doesn't block n8n"""
    print(f"Background process started for: {meeting_url}")
    
    with sync_playwright() as p:
        # Launching with persistent context to skip future logins
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
        
        # --- 1. AUTO-LOGIN CHECK ---
        try:
            # Check if password field exists
            password_input = page.locator('input[type="password"]').first
            password_input.wait_for(state="visible", timeout=5000)
            
            print("Password screen detected. Entering password...")
            password_input.fill("#Possible1")
            page.keyboard.press("Enter")
            page.wait_for_load_state("networkidle")
        except Exception:
            print("No login required or already logged in.")

        # Wait for UI to settle
        page.wait_for_timeout(5000) 

        # --- 2. MUTE MICROPHONE ---
        try:
            mic_button = page.locator('[aria-label*="microphone" i]').first
            mic_button.click(timeout=3000)
            print("Microphone muted.")
        except Exception:
            page.mouse.click(420, 660) # Coordinate fallback
            
        page.wait_for_timeout(1000)

        # --- 3. MUTE CAMERA ---
        try:
            cam_button = page.locator('[aria-label*="camera" i]').first
            cam_button.click(timeout=3000)
            print("Camera turned off.")
        except Exception:
            page.mouse.click(480, 660) # Coordinate fallback

        page.wait_for_timeout(1000)

        # --- 4. JOIN BUTTON ---
        join_texts = ["Join now", "Ask to join", "Switch here", "Join"]
        joined = False
        
        for text in join_texts:
            try:
                locator = page.get_by_text(text, exact=True).first
                if locator.is_visible(timeout=2000):
                    locator.click()
                    print(f"Clicked '{text}' button.")
                    joined = True
                    break
            except Exception:
                continue
        
        if not joined:
            page.mouse.click(900, 450) # Coordinate fallback
            print("Clicked Join area via coordinates.")

        # Keep browser open for 1 hour
        print("Bot is now in the meeting. Background thread will stay alive for 1 hour.")
        page.wait_for_timeout(3600000) 
        
        browser_context.close()
        print("1 hour reached. Browser closed.")

@app.route('/join', methods=['POST'])
def join_meeting():
    data = request.json
    meeting_url = data.get('url')

    if not meeting_url:
        return jsonify({"error": "No meeting URL provided"}), 400

    # START THE THREAD: This is the critical part!
    # It launches the browser logic but returns a response to n8n immediately.
    bot_thread = threading.Thread(target=run_browser_logic, args=(meeting_url,))
    bot_thread.start()

    print("Success response sent to n8n. Browser is handling the rest...")
    return jsonify({
        "status": "success", 
        "message": "Bot is joining the meeting in the background!"
    }), 200

if __name__ == '__main__':
    # Listen on 0.0.0.0 so Docker can communicate
    app.run(host='0.0.0.0', port=5000)
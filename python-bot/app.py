from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright
import os

app = Flask(__name__)

USER_DATA_DIR = os.path.join(os.getcwd(), "browser_profile")

@app.route('/join', methods=['POST'])
def join_meeting():
    data = request.json
    meeting_url = data.get('url')

    if not meeting_url:
        return jsonify({"error": "No meeting URL provided"}), 400

    print(f"Booting up browser for: {meeting_url}")

    with sync_playwright() as p:
        browser_context = p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=False,
            permissions=['camera', 'microphone'],
            args=[
                "--disable-blink-features=AutomationControlled",
                "--use-fake-ui-for-media-stream", 
                "--use-fake-device-for-media-stream"
            ] 
        )
        
        page = browser_context.pages[0]
        page.goto(meeting_url)
        
        print("Page loaded. Waiting 5 seconds for UI to settle...")
        page.wait_for_timeout(5000) 

        # --- 1. CLICK UI BUTTONS TO MUTE ---
        print("Looking for UI buttons to mute mic and camera...")
        
        # Target any element where the aria-label contains the word 'microphone'
        try:
            mic_button = page.locator('[aria-label*="microphone" i]').first
            if mic_button.is_visible(timeout=3000):
                mic_button.click()
                print("Successfully clicked the Microphone UI button.")
            else:
                print("Microphone button not visible.")
        except Exception as e:
            print(f"Failed to click microphone: {e}")

        page.wait_for_timeout(1000)

        # Target any element where the aria-label contains the word 'camera'
        try:
            cam_button = page.locator('[aria-label*="camera" i]').first
            if cam_button.is_visible(timeout=3000):
                cam_button.click()
                print("Successfully clicked the Camera UI button.")
            else:
                print("Camera button not visible.")
        except Exception as e:
            print(f"Failed to click camera: {e}")

        page.wait_for_timeout(1000)

        # --- 2. CLICK THE JOIN BUTTON ---
        print("Looking for the join button...")
        join_texts = ["Join now", "Ask to join", "Switch here", "Join"]
        
        joined = False
        for text in join_texts:
            try:
                locator = page.get_by_text(text, exact=True).first
                if locator.is_visible(timeout=1000):
                    locator.click()
                    print(f"Successfully clicked: '{text}'")
                    joined = True
                    break
            except Exception:
                continue
        
        if not joined:
            print("Could not find a join button. We might already be inside the meeting.")
        
        # Hold the meeting open for an hour (3600000 ms)
        page.wait_for_timeout(3600000) 
        
        browser_context.close()

    return jsonify({"status": "success", "message": "Attended meeting!"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
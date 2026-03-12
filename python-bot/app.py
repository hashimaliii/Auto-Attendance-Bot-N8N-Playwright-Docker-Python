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
            viewport={'width': 1280, 'height': 720}, # Required for coordinate fallback
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

        # --- 1. DUAL-METHOD MICROPHONE MUTE ---
        print("Attempting to mute Microphone...")
        try:
            # Strategy A: Try the smart DOM locator first
            mic_button = page.locator('[aria-label*="microphone" i]').first
            mic_button.click(timeout=3000)
            print("Success: Clicked Microphone via DOM label.")
        except Exception:
            # Strategy B: Fallback to raw coordinates if DOM fails
            print("DOM locator failed. Falling back to coordinates...")
            mic_x = 420  # <-- REPLACE WITH YOUR X
            mic_y = 660  # <-- REPLACE WITH YOUR Y
            page.mouse.click(mic_x, mic_y)
            print("Success: Clicked Microphone via coordinates.")
            
        page.wait_for_timeout(1000)

        # --- 2. DUAL-METHOD CAMERA MUTE ---
        print("Attempting to turn off Camera...")
        try:
            # Strategy A: Try the smart DOM locator first
            cam_button = page.locator('[aria-label*="camera" i]').first
            cam_button.click(timeout=3000)
            print("Success: Clicked Camera via DOM label.")
        except Exception:
            # Strategy B: Fallback to raw coordinates if DOM fails
            print("DOM locator failed. Falling back to coordinates...")
            cam_x = 480  # <-- REPLACE WITH YOUR X
            cam_y = 660  # <-- REPLACE WITH YOUR Y
            page.mouse.click(cam_x, cam_y)
            print("Success: Clicked Camera via coordinates.")

        page.wait_for_timeout(1000)

        # --- 3. DUAL-METHOD JOIN BUTTON ---
        print("Looking for the join button...")
        join_texts = ["Join now", "Ask to join", "Switch here", "Join"]
        joined = False
        
        # Strategy A: Look for the text
        for text in join_texts:
            try:
                locator = page.get_by_text(text, exact=True).first
                if locator.is_visible(timeout=1500):
                    locator.click()
                    print(f"Success: Clicked '{text}' via text locator.")
                    joined = True
                    break
            except Exception:
                continue
        
        # Strategy B: Fallback to raw coordinates for the Join button
        if not joined:
            print("Text locator failed. Falling back to Join button coordinates...")
            join_x = 900  # <-- You may want to find the real X/Y for your join button
            join_y = 450  # <-- You may want to find the real X/Y for your join button
            page.mouse.click(join_x, join_y)
            print("Clicked Join area via coordinates. We might be in.")
        
        page.wait_for_timeout(3600000) 
        
        browser_context.close()

    return jsonify({"status": "success", "message": "Attended meeting!"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
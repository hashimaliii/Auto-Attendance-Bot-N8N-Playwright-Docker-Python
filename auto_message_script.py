import pyautogui
import time

# Configuration
MESSAGE = "Hey, the class link is https://meet.google.com/wiq-krmb-cxd"
INTERVAL = 30  # seconds

print("Script starting in 5 seconds...")
print("Open WhatsApp Web/Desktop and click into the chat box!")
time.sleep(5)

try:
    while True:
        # Type the message
        pyautogui.write(MESSAGE)
        
        # Press Enter to send
        pyautogui.press('enter')
        
        print(f"Message sent. Waiting {INTERVAL} seconds...")
        
        # Wait for the next round
        time.sleep(INTERVAL)
except KeyboardInterrupt:
    print("\nScript stopped by user.")
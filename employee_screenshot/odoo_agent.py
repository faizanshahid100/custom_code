import os
import base64
import requests
import platform
import subprocess   # <-- add this!
from datetime import datetime
from time import sleep
import pyautogui

# ==========================
# Odoo Config
# ==========================
ODOO_URL = "http://localhost:8069"
ODOO_DB = "prime"
ODOO_USER = "admin"
ODOO_PASS = "pakistan1122"

# ==========================
# Cross-platform screenshot
# ==========================
if platform.system() == "Windows":
    from PIL import ImageGrab

    def capture_screen(filename):
        img = ImageGrab.grab()
        img.save(filename)

else:  # Linux
    import pyautogui
    def capture_screen(filename):
        screenshot = pyautogui.screenshot()
        screenshot.save(filename)

# ==========================
# Get Odoo session
# ==========================
def get_uid():
    url = f"{ODOO_URL}/jsonrpc"
    payload = {
        "jsonrpc": "2.0",
        "method": "call",
        "params": {
            "service": "common",
            "method": "login",
            "args": [ODOO_DB, ODOO_USER, ODOO_PASS],
        },
        "id": 1,
    }
    response = requests.post(url, json=payload).json()
    return response.get("result")

# ==========================
# Send Screenshot
# ==========================
def send_screenshot(uid):
    try:
        filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        capture_screen(filename)

        with open(filename, "rb") as f:
            img_base64 = base64.b64encode(f.read()).decode("utf-8")

        url = f"{ODOO_URL}/jsonrpc"
        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "service": "object",
                "method": "execute_kw",
                "args": [
                    ODOO_DB,
                    uid,
                    ODOO_PASS,
                    "employee.screenshot",
                    "create",
                    [{
                        "user_id": uid,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "screenshot": img_base64,
                        "filename": filename,
                    }]
                ],
            },
            "id": 2,
        }
        requests.post(url, json=payload)
        print(f"[OK] Sent {filename} to Odoo")

        os.remove(filename)

    except Exception as e:
        print(f"[ERROR] {e}")

# ==========================
# Main Loop
# ==========================
if __name__ == "__main__":
    uid = get_uid()
    if not uid:
        print("[ERROR] Failed to login to Odoo")
        exit(1)

    print(f"[INFO] Logged in as UID {uid}")

    while True:
        send_screenshot(uid)
        sleep(10)  # every 10 minutes

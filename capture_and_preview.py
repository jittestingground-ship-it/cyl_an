from playwright.sync_api import sync_playwright
import sys
import os
import requests
from find_external_drive import find_external_drive

# Get order ID from command-line argument
if len(sys.argv) < 2:
    print("Usage: python capture_and_preview.py <ORDER_ID>")
    sys.exit(1)
ORDER_ID = sys.argv[1]

REPORT_URL = f"http://localhost:5050/report/{ORDER_ID}"  # Replace ORDER_ID as needed
EMAIL_PREVIEW_URL = f"http://localhost:5050/email_preview/{ORDER_ID}"  # Replace ORDER_ID as needed

ext_drive = find_external_drive()
image_dir = os.path.join(ext_drive, "report_images")
os.makedirs(image_dir, exist_ok=True)
image_path = os.path.join(image_dir, f"{ORDER_ID}.png")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    # 1. Go to the report page and capture screenshot
    page.goto(REPORT_URL)
    page.wait_for_load_state('networkidle')
    page.screenshot(path=image_path, full_page=True)
    img_tag = f'<img src="file://{image_path}" style="width:100vw;height:100vh;object-fit:cover;display:block;">'

    # 2. Go to the email preview page and replace body with the image
    preview_page = browser.new_page()
    preview_page.goto(EMAIL_PREVIEW_URL)
    preview_page.wait_for_load_state('networkidle')
    preview_page.evaluate(f"document.body.innerHTML = `{img_tag}`;")
    browser.close()
    
    # 3. Automatically send the email
    try:
        response = requests.post(f'http://localhost:5050/send_email/{ORDER_ID}', timeout=10)
        if response.status_code == 200:
            result = response.json()
            if 'status' in result and 'Error' not in result['status']:
                print(f"✅ Email sent successfully for order {ORDER_ID}")
            else:
                print(f"⚠️ Email send failed: {result}")
        else:
            print(f"⚠️ Email send failed with status: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Could not send email: {e}")
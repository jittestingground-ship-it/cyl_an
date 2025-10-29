from flask import Flask, send_file, Response, request
import smtplib
from email.message import EmailMessage
import os
from playwright.sync_api import sync_playwright
import io

app = Flask(__name__)


@app.route('/email_preview')
def email_preview():
    # Minimal preview page that shows only the captured report image
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Email Preview</title>
        <style>
            body { margin: 0; padding: 0; background: #fff; }
            .preview-img { display: block; margin: 0 auto; max-width: 100vw; max-height: 100vh; }
        </style>
    </head>
    <body>
        <img class="preview-img" src="/capture-report" alt="Report Snapshot" />
    </body>
    </html>
    '''


@app.route('/capture-report')
def capture_report():
    """
    Capture the `/report` page using Playwright and return a PNG image.
    Before capturing, find the HDF5 file for the order ID on the external drive and save the image in the same directory.
    Usage: /capture-report?order_id=J1023251233&data_dir=/mnt/external_drive/test_data
    """
    order_id = request.args.get('order_id')
    data_dir = request.args.get('data_dir')
    if not order_id:
        return Response("Missing order_id parameter", status=400, mimetype='text/plain')
    # Use provided data_dir or fallback to current directory
    if data_dir and os.path.exists(data_dir):
        save_dir = data_dir
    else:
        save_dir = os.path.dirname(os.path.abspath(__file__))
    img_path = os.path.join(save_dir, f"{order_id}.jpg")
    if os.path.exists(img_path):
        import time
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        img_path = os.path.join(save_dir, f"{order_id}_{timestamp}.jpg")
    try:
        import time
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=['--no-sandbox'])
            page = browser.new_page()
            page.goto(f'http://localhost:5050/report?order_id={order_id}', wait_until='networkidle', timeout=30000)
            time.sleep(3)  # Wait 3 seconds for page to fully build
            img_bytes = page.screenshot(full_page=True, type='jpeg', quality=90)
            browser.close()
        with open(img_path, 'wb') as f:
            f.write(img_bytes)
        # Send email with image attached
        send_report_email(img_bytes, order_id)
        return Response(img_bytes, mimetype='image/jpeg')
    except Exception as e:
        return Response(f"Error capturing report: {e}", status=500, mimetype='text/plain')

def send_report_email(img_bytes, order_id):
    try:
        msg = EmailMessage()
        msg['Subject'] = f'Report Snapshot for Order {order_id}'
        msg['From'] = 'noreply@jitindustries.com'
        msg['To'] = 'kane@jitindustries.com'
        msg.set_content(f'Attached is the report snapshot for order {order_id}.')
        msg.add_attachment(img_bytes, maintype='image', subtype='jpeg', filename=f'{order_id}.jpg')
        # Update SMTP server details as needed
        with smtplib.SMTP('localhost') as s:
            s.send_message(msg)
    except Exception as e:
        print(f"Error sending email: {e}")
def find_external_drive():
    # On Linux, external drives are usually mounted under /mnt or /media
    # This function is now unused, but kept for compatibility
    return os.path.dirname(os.path.abspath(__file__))


def main():
    import sys
    if len(sys.argv) < 3:
        print("Usage: python capture_report.py <order_id> <report_url> [save_dir]")
        sys.exit(1)
    order_id = sys.argv[1]
    report_url = sys.argv[2]
    if len(sys.argv) > 3:
        save_dir = sys.argv[3]
    else:
        save_dir = os.path.dirname(os.path.abspath(__file__))
    img_path = os.path.join(save_dir, f"{order_id}.jpg")
    try:
        import time
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=['--no-sandbox'])
            page = browser.new_page()
            page.goto(report_url, wait_until='networkidle', timeout=30000)
            time.sleep(3)
            img_bytes = page.screenshot(full_page=True, type='jpeg', quality=90)
            browser.close()
        with open(img_path, 'wb') as f:
            f.write(img_bytes)
        print(f"Report image saved to {img_path}")
        sys.exit(0)
    except Exception as e:
        print(f"Error capturing report: {e}")
        sys.exit(2)

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        main()
    else:
        app.run(port=5050)

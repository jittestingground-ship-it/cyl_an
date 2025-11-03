from flask import Flask, request, jsonify
import os
import subprocess
import time
import urllib.request
import socket

app = Flask(__name__)

# Set the path to your external hard drive
EXTERNAL_DRIVE_PATH = "/home/kw/cyl_a/excel_data"

os.makedirs(EXTERNAL_DRIVE_PATH, exist_ok=True)

def check_internet_connectivity():
    """Check if we have internet connectivity by trying to reach a reliable host."""
    try:
        # Try to connect to Google's DNS server
        socket.create_connection(("8.8.8.8", 53), timeout=5)
        return True
    except OSError:
        return False

def connect_wifi():
    """Attempt to connect to WiFi using nmcli."""
    try:
        # Check current WiFi status
        result = subprocess.run(['nmcli', 'radio', 'wifi'], capture_output=True, text=True, timeout=10)
        if 'enabled' not in result.stdout:
            # Enable WiFi if disabled
            subprocess.run(['nmcli', 'radio', 'wifi', 'on'], timeout=10)

        # Try to connect to known networks
        result = subprocess.run(['nmcli', 'device', 'wifi', 'connect'], capture_output=True, text=True, timeout=15)
        return 'successfully' in result.stdout.lower() or result.returncode == 0
    except subprocess.TimeoutExpired:
        return False
    except Exception as e:
        print(f"WiFi connection error: {e}")
        return False

def enable_rpi_connect_vnc():
    try:
        print("Enabling Raspberry Pi Connect VNC...")
        # rpi-connect should already be running as a service
        result = subprocess.run(['rpi-connect', 'vnc', 'on'], capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            print("✅ Raspberry Pi Connect VNC enabled successfully!")
            return True
        else:
            print(f"⚠️ rpi-connect vnc command returned: {result.stderr.strip()}")
            # Try alternative: check if VNC is already enabled
            status_result = subprocess.run(['rpi-connect', 'status'], capture_output=True, text=True, timeout=10)
            if 'VNC: enabled' in status_result.stdout:
                print("✅ VNC appears to already be enabled")
                return True
            return False
    except subprocess.TimeoutExpired:
        print("❌ rpi-connect command timed out")
        return False
    except FileNotFoundError:
        print("❌ rpi-connect command not found")
        return False
    except Exception as e:
        print(f"❌ Error enabling rpi-connect VNC: {e}")
        return False

def wait_for_wifi_connection(max_attempts=10, check_interval=5):
    """Wait for WiFi connection to be established and stable."""
    print("Checking WiFi connectivity...")

    for attempt in range(max_attempts):
        if check_internet_connectivity():
            print("✅ WiFi connected and internet accessible!")
            # Wait a bit more to ensure stability
            time.sleep(2)
            return True

        print(f"❌ No internet connection (attempt {attempt + 1}/{max_attempts})")

        if attempt < max_attempts - 1:  # Don't try to connect on the last attempt
            print("Attempting to connect to WiFi...")
            if connect_wifi():
                print("WiFi connection attempt successful, waiting for internet...")
                time.sleep(check_interval)
            else:
                print("WiFi connection attempt failed, retrying...")
                time.sleep(check_interval)

    print("❌ Failed to establish stable WiFi connection after all attempts")
    return False
@app.route("/upload_excel", methods=["POST"])
def upload_excel():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if file and (file.filename.endswith('.xlsx') or file.filename.endswith('.xls')):
        save_path = os.path.join(EXTERNAL_DRIVE_PATH, file.filename)
        file.save(save_path)
        return jsonify({"message": f"File saved to {save_path}"}), 200
    return jsonify({"error": "Invalid file type"}), 400

if __name__ == "__main__":
    # Ensure WiFi is connected before starting the server
    if not wait_for_wifi_connection():
        print("Cannot start Excel upload server: No stable WiFi connection available")
        exit(1)

    # Enable Raspberry Pi Connect VNC/screen sharing
    print("DEBUG: About to enable rpi-connect VNC...")
    enable_rpi_connect_vnc()
    print("DEBUG: rpi-connect VNC setup complete")

    print("Starting Excel Upload Server on port 5000...")
    app.run(host="0.0.0.0", port=5000)
    
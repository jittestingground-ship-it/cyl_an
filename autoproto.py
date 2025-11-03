import os
import subprocess
import sys
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, jsonify
import h5py  # Ensure h5py is installed: pip install h5py
import random
import smtplib
import json
import glob

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

def find_external_drive():
    """Find external drive on Linux systems."""
    # Common Linux mount points for external drives
    mount_points = ["/media/kw", "/mnt", "/media"]
    for mount_point in mount_points:
        if os.path.exists(mount_point):
            try:
                for entry in os.listdir(mount_point):
                    drive_path = os.path.join(mount_point, entry)
                    if os.path.ismount(drive_path):
                        return drive_path
            except PermissionError:
                continue
    # Fallback to BASE_DIR if no external drive found
    return BASE_DIR
EXT_DRIVE = find_external_drive()
EXT_PATH = os.path.join(EXT_DRIVE, "autoproto_data")
EXT_EXCEL_DATA = os.path.join(EXT_DRIVE, "excel_data")
EXT_TEST_DATA = os.path.join(EXT_DRIVE, "test_data")
EXT_REPORT_IMAGES = os.path.join(EXT_DRIVE, "report_images")

# Create external directories if they don't exist
for ext_dir in [EXT_PATH, EXT_EXCEL_DATA, EXT_TEST_DATA, EXT_REPORT_IMAGES]:
    if not os.path.exists(ext_dir):
        os.makedirs(ext_dir)

DB_PATH = os.path.join(EXT_PATH, "OrderData.db")
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    orderID TEXT NOT NULL UNIQUE,
    name TEXT,
    email TEXT,
    phone TEXT,
    address TEXT
)''')
c.execute('''CREATE TABLE IF NOT EXISTS testing_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id TEXT NOT NULL,
    file_path TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)''')
conn.commit()
conn.close()




# Commented out fake orders - only show Excel data
# add_fake_order("J1002251124")
# add_fake_order("J1002251125")
# add_fake_order("J1002251126")

# Email configuration
DEFAULT_EMAIL = "kane@jitindustries.com"

app = Flask(__name__)

# Route for /dashboard to serve the colored dashboard page
@app.route("/dashboard")
def dashboard_colored():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    orders = c.execute("SELECT * FROM orders").fetchall()
    tests = c.execute("SELECT * FROM testing_files").fetchall()
    conn.close()
    # Read Excel data files and sort by timestamp (newest first)
    excel_data = []
    excel_files = glob.glob(os.path.join(EXT_EXCEL_DATA, "*.json"))
    file_data = []
    for file_path in excel_files:
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                data['filename'] = os.path.basename(file_path)
                filename = os.path.basename(file_path)
                timestamp_str = filename.replace('excel_data_', '').replace('.json', '')
                file_data.append((timestamp_str, data))
        except:
            pass
    file_data.sort(key=lambda x: x[0], reverse=True)
    excel_data = [item[1] for item in file_data]
    return render_template("dashboard_colored.html", orders=orders, tests=tests, excel_data=excel_data)

@app.route("/")
def dashboard():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    orders = c.execute("SELECT * FROM orders").fetchall()
    tests = c.execute("SELECT * FROM testing_files").fetchall()
    conn.close()
    
    # Read Excel data files and sort by timestamp (newest first)
    excel_data = []
    excel_files = glob.glob(os.path.join(EXT_EXCEL_DATA, "*.json"))
    
    # Extract timestamp from filename and sort
    file_data = []
    for file_path in excel_files:
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                data['filename'] = os.path.basename(file_path)
                
                # Extract timestamp from filename (excel_data_YYYYMMDD_HHMMSS.json)
                filename = os.path.basename(file_path)
                timestamp_str = filename.replace('excel_data_', '').replace('.json', '')
                file_data.append((timestamp_str, data))
        except:
            pass
    
    # Sort by timestamp (newest first) and extract data
    file_data.sort(key=lambda x: x[0], reverse=True)
    excel_data = [item[1] for item in file_data]
    
    return render_template("rootdashboard.html", orders=orders, tests=tests, excel_data=excel_data)

@app.route("/details/<order_id>")
def details(order_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    order = c.execute("SELECT * FROM orders WHERE orderID=?", (order_id,)).fetchone()
    test_file = c.execute("SELECT file_path FROM testing_files WHERE order_id=?", (order_id,)).fetchone()
    conn.close()
    
    # If order not in database, check if it's from Excel data
    if not order:
        # Look for Excel data with this order ID
        excel_files = glob.glob(os.path.join(EXT_EXCEL_DATA, "*.json"))
        for file_path in excel_files:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    if data.get('orderID') == order_id:
                        # Create fake order tuple to match database format
                        order = (None, data.get('orderID'), data.get('name'), 
                                data.get('email'), data.get('phone'), data.get('address'))
                        break
            except:
                pass
    
    chart_data = {"pressure_a": [], "pressure_b": [], "timestamp": []}
    meta = {}
    
    # First check database for test file
    if test_file:
        try:
            with h5py.File(test_file[0], "r") as f:
                chart_data["pressure_a"] = f["data/pressure_a"][:].tolist()
                chart_data["pressure_b"] = f["data/pressure_b"][:].tolist()
                chart_data["timestamp"] = f["data/timestamp"][:].tolist()
                m = f["metadata"].attrs
                meta = dict(m.items())
        except:
            test_file = None
    
    # If no database file, look in test_data folder where scanner saves
    if not test_file:
        test_data_dir = EXT_TEST_DATA
        if os.path.exists(test_data_dir):
            # Find H5 files matching this order ID
            h5_files = glob.glob(f"{test_data_dir}/{order_id}_*.h5")
            if h5_files:
                # Use the most recent file
                latest_file = max(h5_files, key=os.path.getctime)
                try:
                    with h5py.File(latest_file, "r") as f:
                        # Read data arrays
                        pressure_a_data = f["data/pressure_a"][:]
                        pressure_b_data = f["data/pressure_b"][:]
                        timestamp_data = f["data/timestamp"][:]
                        
                        # Convert to Python lists for JSON serialization
                        chart_data["pressure_a"] = [float(x) for x in pressure_a_data]
                        chart_data["pressure_b"] = [float(x) for x in pressure_b_data]
                        chart_data["timestamp"] = [float(x) for x in timestamp_data]
                        
                        print(f"DEBUG: Loaded {len(chart_data['pressure_a'])} samples from {latest_file}")
                        print(f"DEBUG: Pressure A range: {min(chart_data['pressure_a'])}-{max(chart_data['pressure_a'])}")
                        print(f"DEBUG: Timestamp range: {min(chart_data['timestamp'])}-{max(chart_data['timestamp'])}")
                        
                        # Convert timestamps from milliseconds to seconds for chart
                        if chart_data["timestamp"]:
                            # Check if timestamps are in milliseconds (large numbers)
                            if max(chart_data["timestamp"]) > 100000:
                                # Convert to seconds and normalize to start at 0
                                start_time = min(chart_data["timestamp"]) / 1000
                                chart_data["timestamp"] = [(t/1000) - start_time for t in chart_data["timestamp"]]
                            else:
                                # Already in seconds, normalize to start at 0  
                                start_time = min(chart_data["timestamp"])
                                chart_data["timestamp"] = [t - start_time for t in chart_data["timestamp"]]
                        
                        # Create metadata from H5 file
                        if "metadata" in f:
                            try:
                                order_id_data = f["metadata/order_id"][()]
                                if isinstance(order_id_data, bytes):
                                    order_id_data = order_id_data.decode('utf-8')
                                samples = f["metadata/samples"][()]
                                saved_at_data = f["metadata/saved_at"][()]
                                if isinstance(saved_at_data, bytes):
                                    saved_at_data = saved_at_data.decode('utf-8')
                                
                                # Calculate test metrics
                                pa_avg = sum(chart_data["pressure_a"]) / len(chart_data["pressure_a"])
                                pb_avg = sum(chart_data["pressure_b"]) / len(chart_data["pressure_b"])
                                max_diff = max(abs(a-b) for a,b in zip(chart_data["pressure_a"], chart_data["pressure_b"]))
                                
                                meta = {
                                    "order_id": order_id_data,
                                    "samples": int(samples),
                                    "saved_at": saved_at_data,
                                    "set_pressure": 70.0,
                                    "avg_pressure_a": round(pa_avg, 2),
                                    "avg_pressure_b": round(pb_avg, 2),
                                    "max_leak_pressure": round(max_diff, 2),
                                    "cycle_count": 1,
                                    "test_time": round(max(chart_data["timestamp"]) - min(chart_data["timestamp"]), 1),
                                    "test_pass_fail": 1 if max_diff < 5 else 0
                                }
                            except:
                                meta = {"samples": len(chart_data["pressure_a"]), "message": "Test data found"}
                        else:
                            meta = {"samples": len(chart_data["pressure_a"]), "message": "Test data found"}
                except Exception as e:
                    meta = {"message": f"Error reading test file: {str(e)}"}
    
    # If still no test data found
    if not meta or (not chart_data["timestamp"] and "message" not in meta):
        meta = {"message": "No test data available for this order"}
        
    return render_template("details.html", order=order, meta=meta, chart_data=chart_data)



@app.route("/report/<order_id>")
def report(order_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    order = c.execute("SELECT * FROM orders WHERE orderID=?", (order_id,)).fetchone()
    test_file = c.execute("SELECT file_path FROM testing_files WHERE order_id=?", (order_id,)).fetchone()
    conn.close()
    # If order not in database, check if it's from Excel data
    if not order:
        excel_files = glob.glob(os.path.join(EXT_EXCEL_DATA, "*.json"))
        for file_path in excel_files:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    if data.get('orderID') == order_id:
                        order = (None, data.get('orderID'), data.get('name'), 
                                data.get('email'), data.get('phone'), data.get('address'))
                        break
            except:
                pass
    chart_data = {"pressure_a": [], "pressure_b": [], "timestamp": []}
    meta = {}
    # First check database for test file
    if test_file:
        try:
            with h5py.File(test_file[0], "r") as f:
                chart_data["pressure_a"] = f["data/pressure_a"][:].tolist()
                chart_data["pressure_b"] = f["data/pressure_b"][:].tolist()
                chart_data["timestamp"] = f["data/timestamp"][:].tolist()
                m = f["metadata"].attrs
                meta = dict(m.items())
        except:
            test_file = None
    # If no database file, look in test_data folder where scanner saves
    if not test_file:
        test_data_dir = EXT_TEST_DATA
        if os.path.exists(test_data_dir):
            h5_files = glob.glob(f"{test_data_dir}/{order_id}_*.h5")
            if h5_files:
                latest_file = max(h5_files, key=os.path.getctime)
                try:
                    with h5py.File(latest_file, "r") as f:
                        pressure_a_data = f["data/pressure_a"][:]
                        pressure_b_data = f["data/pressure_b"][:]
                        timestamp_data = f["data/timestamp"][:]
                        chart_data["pressure_a"] = [float(x) for x in pressure_a_data]
                        chart_data["pressure_b"] = [float(x) for x in pressure_b_data]
                        chart_data["timestamp"] = [float(x) for x in timestamp_data]
                        # Convert timestamps from ms to s for chart
                        if chart_data["timestamp"]:
                            if max(chart_data["timestamp"]) > 100000:
                                start_time = min(chart_data["timestamp"]) / 1000
                                chart_data["timestamp"] = [(t/1000) - start_time for t in chart_data["timestamp"]]
                            else:
                                start_time = min(chart_data["timestamp"])
                                chart_data["timestamp"] = [t - start_time for t in chart_data["timestamp"]]
                        # Create metadata from H5 file
                        if "metadata" in f:
                            try:
                                order_id_data = f["metadata/order_id"][()]
                                if isinstance(order_id_data, bytes):
                                    order_id_data = order_id_data.decode('utf-8')
                                samples = f["metadata/samples"][()]
                                saved_at_data = f["metadata/saved_at"][()]
                                if isinstance(saved_at_data, bytes):
                                    saved_at_data = saved_at_data.decode('utf-8')
                                pa_avg = sum(chart_data["pressure_a"]) / len(chart_data["pressure_a"])
                                pb_avg = sum(chart_data["pressure_b"]) / len(chart_data["pressure_b"])
                                max_diff = max(abs(a-b) for a,b in zip(chart_data["pressure_a"], chart_data["pressure_b"]))
                                meta = {
                                    "order_id": order_id_data,
                                    "samples": int(samples),
                                    "saved_at": saved_at_data,
                                    "set_pressure": 70.0,
                                    "avg_pressure_a": round(pa_avg, 2),
                                    "avg_pressure_b": round(pb_avg, 2),
                                    "max_leak_pressure": round(max_diff, 2),
                                    "cycle_count": 1,
                                    "test_time": round(max(chart_data["timestamp"]) - min(chart_data["timestamp"]), 1),
                                    "test_pass_fail": 1 if max_diff < 5 else 0
                                }
                            except:
                                meta = {"samples": len(chart_data["pressure_a"]), "message": "Test data found"}
                        else:
                            meta = {"samples": len(chart_data["pressure_a"]), "message": "Test data found"}
                except Exception as e:
                    meta = {"message": f"Error reading test file: {str(e)}"}
    # If still no test data found
    if not meta or (not chart_data["timestamp"] and "message" not in meta):
        meta = {"message": "No test data available for this order"}
    return render_template("report.html", order=order, meta=meta, chart_data=chart_data)

import subprocess

@app.route('/trigger_capture_report/<order_id>', methods=['POST'])
def trigger_capture_report(order_id):
    # Run the Playwright script for the given order ID
    result = subprocess.run(
        ['/home/kw/cyl_a/venv/bin/python', 'capture_and_preview.py', order_id],
        cwd='/home/kw/cyl_a',
        capture_output=True,
        text=True
    )
    # You can check result.returncode and result.stdout/stderr if needed
    return jsonify({'status': True, 'message': 'Image processed successfully'})

@app.route('/report_image/<filename>')
def serve_report_image(filename):
    from flask import send_from_directory
    import os
    return send_from_directory(EXT_REPORT_IMAGES, filename)


@app.route('/email_preview/<order_id>')
def email_preview(order_id):
    return render_template('email_preview.html', order_id=order_id)



@app.route("/send_email/<order_id>", methods=["POST"])
def send_email(order_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    order = c.execute("SELECT * FROM orders WHERE orderID=?", (order_id,)).fetchone()
    test_file = c.execute("SELECT file_path FROM testing_files WHERE order_id=?", (order_id,)).fetchone()
    conn.close()
    
    # If order not in database, check Excel data
    if not order:
        excel_files = glob.glob(os.path.join(EXT_EXCEL_DATA, "*.json"))
        for file_path in excel_files:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    if data.get('orderID') == order_id:
                        order = (None, data.get('orderID'), data.get('name'), 
                                data.get('email'), data.get('phone'), data.get('address'))
                        break
            except:
                pass
    
    # Get test results for email body
    test_results = ""
    test_data_dir = EXT_TEST_DATA
    if os.path.exists(test_data_dir):
        h5_files = glob.glob(f"{test_data_dir}/{order_id}_*.h5")
        if h5_files:
            latest_file = max(h5_files, key=os.path.getctime)
            try:
                with h5py.File(latest_file, "r") as f:
                    pressure_a_data = f["data/pressure_a"][:]
                    pressure_b_data = f["data/pressure_b"][:]
                    
                    # Calculate test metrics
                    pa_avg = sum(pressure_a_data) / len(pressure_a_data)
                    pb_avg = sum(pressure_b_data) / len(pressure_b_data)
                    max_diff = max(abs(a-b) for a,b in zip(pressure_a_data, pressure_b_data))
                    samples = len(pressure_a_data)
                    
                    test_results = f"""
TEST RESULTS SUMMARY:
- Samples Collected: {samples}
- Average Pressure A: {pa_avg:.2f} PSI
- Average Pressure B: {pb_avg:.2f} PSI  
- Maximum Pressure Difference: {max_diff:.2f} PSI
- Test Status: {"PASS" if max_diff < 5 else "FAIL"}
"""
            except:
                test_results = "Test data file found but could not be read."
    
    sender = "jitrndhost@gmail.com"
    password = "ddko ocle ezwa gsmt"
    to_addr = DEFAULT_EMAIL
    subject = f"Report Image for Order {order_id}"
    # Find the report image for this order in the external drive
    img_path = os.path.join(EXT_REPORT_IMAGES, f"{order_id}.png")
    if not os.path.exists(img_path):
        return jsonify({"status": "Error", "error": "Report image not found."})
    import email, email.mime.multipart, email.mime.base, email.encoders
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    from email.mime.base import MIMEBase
    from email import encoders
    msg = MIMEMultipart('related')
    msg['From'] = sender
    msg['To'] = to_addr
    msg['Subject'] = subject
    # HTML body with inline image
    html = f"""
    <html>
        <body>
            <p>Report image for order {order_id}:</p>
            <img src=\"cid:reportimage\" style=\"max-width:600px;width:100%;object-fit:contain;\">
        </body>
        </html>
        """
    msg.attach(MIMEText(html, 'html'))
    with open(img_path, 'rb') as f:
            img = MIMEBase('image', 'png')
            img.set_payload(f.read())
            encoders.encode_base64(img)
            img.add_header('Content-ID', '<reportimage>')
            img.add_header('Content-Disposition', 'inline', filename=os.path.basename(img_path))
            msg.attach(img)
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, to_addr, msg.as_string())
        server.quit()
        return jsonify({"status": f"Report image sent to {to_addr}"})
    except Exception as e:
        return jsonify({"status": "Error", "error": str(e)})

@app.route("/store_data", methods=["GET", "POST"])
def store_data():
    try:
        if request.method == "GET":
            return jsonify({"status": "Ready to receive data", "endpoint": "/store_data"})
        else:  # POST
            data = request.get_json()
            # Process incoming Excel data here
            return jsonify({"status": "Data received", "data": data})
    except Exception as e:
        return jsonify({"status": "Error", "error": str(e)})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)



import os
import subprocess
import sys
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, jsonify
import h5py
import random
import smtplib
import json
import glob

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

def find_external_drive():
    from string import ascii_uppercase
    for letter in ascii_uppercase:
        drive = f"{letter}:\\"
        if os.path.exists(drive) and drive != "C:\\":
            return drive
    return BASE_DIR
EXT_DRIVE = find_external_drive()
EXT_PATH = os.path.join(EXT_DRIVE, "autoproto_data")
if not os.path.exists(EXT_PATH):
    os.makedirs(EXT_PATH)

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

def generate_fake_test(order_id):
    h5_path = os.path.join(EXT_PATH, f"{order_id}_test.h5")
    with h5py.File(h5_path, "w") as f:
        grp_data = f.create_group("data")
        times = [i*0.5 for i in range(141)]
        pres_a = [random.uniform(30, 70) for _ in times]
        pres_b = [random.uniform(28, 68) for _ in times]
        grp_data.create_dataset("pressure_a", data=pres_a)
        grp_data.create_dataset("pressure_b", data=pres_b)
        grp_data.create_dataset("timestamp", data=times)
        grp_meta = f.create_group("metadata")
        grp_meta.attrs["order_id"] = order_id
        grp_meta.attrs["set_pressure"] = 70.0
        grp_meta.attrs["avg_pressure_a"] = sum(pres_a)/len(pres_a)
        grp_meta.attrs["avg_pressure_b"] = sum(pres_b)/len(pres_b)
        grp_meta.attrs["max_leak_pressure"] = max(abs(a-b) for a,b in zip(pres_a,pres_b))
        grp_meta.attrs["cycle_count"] = 3
        grp_meta.attrs["test_time"] = 70.5
        grp_meta.attrs["samples"] = len(times)
        grp_meta.attrs["test_pass_fail"] = 1
        grp_meta.attrs["saved_at"] = "2025-10-08T15:30:22"
    return h5_path

def add_fake_order(order_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO orders (orderID, name, email, phone, address) VALUES (?, ?, ?, ?, ?)",
              (order_id, "Kane Industries", "kane@jitindustries.com", "555-1234", "123 Main St"))
    conn.commit()
    conn.close()
    h5_path = generate_fake_test(order_id)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO testing_files (order_id, file_path) VALUES (?, ?)", (order_id, h5_path))
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
    excel_files = glob.glob("/home/kw/cyl_a/excel_data/*.json")
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
    excel_files = glob.glob("/home/kw/cyl_a/excel_data/*.json")
    
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
        excel_files = glob.glob("/home/kw/cyl_a/excel_data/*.json")
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
        test_data_dir = "/home/kw/cyl_a/test_data"
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
        excel_files = glob.glob("/home/kw/cyl_a/excel_data/*.json")
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
        test_data_dir = "/home/kw/cyl_a/test_data"
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






@app.route("/email_preview/<order_id>")
def email_preview(order_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    order = c.execute("SELECT * FROM orders WHERE orderID=?", (order_id,)).fetchone()
    test_file = c.execute("SELECT file_path FROM testing_files WHERE order_id=?", (order_id,)).fetchone()
    conn.close()
    
    # If order not in database, check Excel data
    if not order:
        excel_files = glob.glob("/home/kw/cyl_a/excel_data/*.json")
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
    
    # Look for test data in test_data folder
    test_results = ""
    test_data_dir = "/home/kw/cyl_a/test_data"
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
        else:
            test_results = "No test data available for this order."
    
    body = f"""Dear {order[2] if order else 'Customer'},

Your cylinder test for Order ID: {order_id} has been completed.

ORDER DETAILS:
- Order ID: {order[1] if order else order_id}
- Customer: {order[2] if order else 'N/A'}
- Email: {order[3] if order else 'N/A'}
- Phone: {order[4] if order else 'N/A'}

{test_results}

Please contact us if you have any questions about your test results.

Best regards,
JIT Industries Test Department
"""
    
    subject = f"Test Results Complete - Order {order_id}"
    
    # Get chart data for email preview
    chart_data = {"pressure_a": [], "pressure_b": [], "timestamp": []}
    if os.path.exists(test_data_dir):
        h5_files = glob.glob(f"{test_data_dir}/{order_id}_*.h5")
        if h5_files:
            latest_file = max(h5_files, key=os.path.getctime)
            try:
                with h5py.File(latest_file, "r") as f:
                    chart_data["pressure_a"] = [float(x) for x in f["data/pressure_a"][:]]
                    chart_data["pressure_b"] = [float(x) for x in f["data/pressure_b"][:]]
                    chart_data["timestamp"] = [float(x) for x in f["data/timestamp"][:]]
            except:
                pass
    
    return render_template("email_preview.html", subject=subject, body=body, test_file=latest_file if 'latest_file' in locals() else None, chart_data=chart_data)

@app.route("/send_email/<order_id>", methods=["POST"])
def send_email(order_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    order = c.execute("SELECT * FROM orders WHERE orderID=?", (order_id,)).fetchone()
    test_file = c.execute("SELECT file_path FROM testing_files WHERE order_id=?", (order_id,)).fetchone()
    conn.close()
    
    # If order not in database, check Excel data
    if not order:
        excel_files = glob.glob("/home/kw/cyl_a/excel_data/*.json")
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
    test_data_dir = "/home/kw/cyl_a/test_data"
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
    # Find the latest PNG image for this order
    test_data_dir = "/home/kw/cyl_a/test_data"
    img_path = None
    if os.path.exists(test_data_dir):
        png_files = glob.glob(f"{test_data_dir}/{order_id}*.png")
        if png_files:
            img_path = max(png_files, key=os.path.getctime)
    if not img_path or not os.path.exists(img_path):
        return jsonify({"status": "Error", "error": "Report image not found."})
    import email, email.mime.multipart, email.mime.base, email.encoders
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    from email.mime.base import MIMEBase
    from email import encoders
    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = to_addr
    msg['Subject'] = subject
    msg.attach(MIMEText(f"Attached is the report image for order {order_id}.", 'plain'))
    with open(img_path, 'rb') as f:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename="{os.path.basename(img_path)}"')
        msg.attach(part)
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


# Endpoint to trigger only report capture (not email send)
@app.route('/trigger_capture_report/<order_id>', methods=['POST'])
def trigger_capture_report(order_id):
    # Find the .h5 file for this order in autoproto_data
    ext_drive = find_external_drive()
    ext_path = os.path.join(ext_drive, "autoproto_data")
    h5_path = os.path.join(ext_path, f"{order_id}_test.h5")
    save_dir = ext_path if os.path.exists(h5_path) else os.path.dirname(os.path.abspath(__file__))
    img_path = os.path.join(save_dir, f"{order_id}.jpg")

    print(f"captured report for {order_id} in {save_dir}")

    try:
        # Call the capture_report.py script to generate the report image in the order's data dir
        result = subprocess.run([
            os.path.join(os.path.dirname(__file__), 'venv', 'bin', 'python'),
            os.path.join(os.path.dirname(__file__), 'capture_report.py'),
            order_id,
            f'http://localhost:5050/report/{order_id}',
            save_dir
        ], capture_output=True, text=True)
        if result.returncode == 0 and os.path.exists(img_path):
            # Record image path in testing_files table
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("INSERT INTO testing_files (order_id, file_path) VALUES (?, ?)", (order_id, img_path))
            conn.commit()
            conn.close()
            return jsonify({'status': 'Report captured and saved.', 'image_path': img_path})
        else:
            return jsonify({'error': result.stderr or 'Failed to capture report.'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Endpoint to trigger report email for an order
@app.route('/trigger_report_email/<order_id>', methods=['POST'])
def trigger_report_email(order_id):
    try:
        # Call the capture_report.py script to generate and send the report image
        result = subprocess.run([
            os.path.join(os.path.dirname(__file__), 'venv', 'bin', 'python'),
            os.path.join(os.path.dirname(__file__), 'capture_report.py'),
            order_id,
            f'http://localhost:5050/report/{order_id}'
        ], capture_output=True, text=True)
        if result.returncode == 0:
            return jsonify({'status': 'Report email sent successfully.'})
        else:
            return jsonify({'error': result.stderr or 'Failed to send report email.'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    import traceback
    try:
        app.run(host="0.0.0.0", port=5050)
    except Exception as e:
        # Write error flag for system monitor
        with open("/home/kw/cyl_a/dashboard_error.flag", "w") as f:
            f.write(f"Dashboard error: {str(e)}\n{traceback.format_exc()}")
        raise

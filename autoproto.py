import os
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

app = Flask(__name__)

@app.route("/")
def dashboard():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    orders = c.execute("SELECT * FROM orders").fetchall()
    tests = c.execute("SELECT * FROM testing_files").fetchall()
    conn.close()
    
    # Read Excel data files
    excel_data = []
    excel_files = glob.glob("/home/kw/cyl_a/excel_data/*.json")
    for file_path in sorted(excel_files, reverse=True):
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                data['filename'] = os.path.basename(file_path)
                excel_data.append(data)
        except:
            pass
    
    return render_template("dashboard.html", orders=orders, tests=tests, excel_data=excel_data)

@app.route("/details/<order_id>")
def details(order_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    order = c.execute("SELECT * FROM orders WHERE orderID=?", (order_id,)).fetchone()
    test_file = c.execute("SELECT file_path FROM testing_files WHERE order_id=?", (order_id,)).fetchone()
    conn.close()
    chart_data = {"pressure_a": [], "pressure_b": [], "timestamp": []}
    meta = {}
    if test_file:
        with h5py.File(test_file[0], "r") as f:
            chart_data["pressure_a"] = f["data/pressure_a"][:].tolist()
            chart_data["pressure_b"] = f["data/pressure_b"][:].tolist()
            chart_data["timestamp"] = f["data/timestamp"][:].tolist()
            m = f["metadata"].attrs
            meta = dict(m.items())
    return render_template("details.html", order=order, meta=meta, chart_data=chart_data)

@app.route("/email_preview/<order_id>")
def email_preview(order_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    order = c.execute("SELECT * FROM orders WHERE orderID=?", (order_id,)).fetchone()
    test_file = c.execute("SELECT file_path FROM testing_files WHERE order_id=?", (order_id,)).fetchone()
    conn.close()
    body = f"Order Report for {order[1]}\nCustomer: {order[2]}\nEmail: {order[3]}\n\nSee attached test results."
    subject = f"Order Test Report: {order[1]}"
    return render_template("email_preview.html", subject=subject, body=body, test_file=test_file[0])

@app.route("/send_email/<order_id>", methods=["POST"])
def send_email(order_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    order = c.execute("SELECT * FROM orders WHERE orderID=?", (order_id,)).fetchone()
    test_file = c.execute("SELECT file_path FROM testing_files WHERE order_id=?", (order_id,)).fetchone()
    conn.close()
    sender = "jitrndhost@gmail.com"
    password = "ddko ocle ezwa gsmt"
    to_addr = "kane@jitindustries.com"
    subject = f"Order Test Report: {order[1]}"
    body = f"Order Report for {order[1]}\nCustomer: {order[2]}\nEmail: {order[3]}\n\nSee attached test results."
    message = f"Subject: {subject}\n\n{body}"
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, to_addr, message)
        server.quit()
        return jsonify({"status": "Email sent"})
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
    app.run(host="0.0.0.0", port=5050)
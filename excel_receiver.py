#!/usr/bin/env python3
from flask import Flask, request, jsonify
import json
import os

app = Flask(__name__)

# Store received data
DATA_DIR = "/home/kw/cyl_a/excel_data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

@app.route("/store_data", methods=["GET", "POST"])
def store_data():
    try:
        if request.method == "GET":
            return jsonify({"status": "Ready to receive Excel data", "port": 5000})
        
        # Handle POST data from Excel
        data = request.get_json()
        if data:
            # Save to file with timestamp
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"excel_data_{timestamp}.json"
            filepath = os.path.join(DATA_DIR, filename)
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            
            return jsonify({"status": "Excel data received", "file": filename})
        else:
            return jsonify({"status": "No data received"})
            
    except Exception as e:
        return jsonify({"status": "Error", "error": str(e)})

@app.route("/")
def index():
    return jsonify({"service": "Excel Data Receiver", "port": 5000})

if __name__ == "__main__":
    print("Starting Excel data receiver on port 5000...")
    app.run(host="0.0.0.0", port=5000, debug=False)
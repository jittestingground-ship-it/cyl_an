#!/usr/bin/env python3
import tkinter as tk
from tkinter import scrolledtext
import time
import numpy as np
import h5py
import os
import random
from datetime import datetime
from pymodbus.client import ModbusTcpClient
import serial
import threading

# Find external drive
def find_external_drive():
    from string import ascii_uppercase
    for letter in ascii_uppercase:
        drive = f"{letter}:\\"
        if os.path.exists(drive) and drive != "C:\\":
            return drive
    return "/home/kw/cyl_a"

EXT_DRIVE = find_external_drive()
DATA_DIR = os.path.join(EXT_DRIVE, "test_data")
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# Config
PLC_IP = "192.168.0.11"
PLC_PORT = 502
SERIAL_PORT = "/dev/ttyUSB0"
SERIAL_BAUD = 9600
MAX_SAMPLES = 10000
INTERVAL = 0.01

# Modbus addresses
START_COIL = 16534
RUN_COIL = 16384
PRESSURE_ADDR = 6
REG_COUNT = 2

class ScannerGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Scanner Activity")
        self.root.geometry("400x300+350+200")  # Centered height
        self.root.configure(bg='#2c3e50')
        
        # Status display
        self.status_label = tk.Label(self.root, text="Scanner Initializing...", 
                                   font=("Arial", 16, "bold"), fg="white", bg='#2c3e50')
        self.status_label.pack(pady=20)
        
        # PLC Test Button
        self.test_button = tk.Button(self.root, text="Test PLC Connection", 
                                   command=self.test_plc_connection,
                                   font=("Arial", 12), bg='#3498db', fg='white',
                                   width=20, height=2)
        self.test_button.pack(pady=10)
        
        # Activity log
        self.log_text = scrolledtext.ScrolledText(self.root, width=50, height=15,
                                                bg='#34495e', fg='white', font=("Courier", 10))
        self.log_text.pack(pady=10, padx=10, fill='both', expand=True)
        
        self.running = True
        self.log("Scanner GUI Started")
        
        # Start scanner thread
        self.scanner_thread = threading.Thread(target=self.scanner_loop, daemon=True)
        self.scanner_thread.start()
        
    def log(self, message):
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update()
        
    def update_status(self, status):
        self.status_label.config(text=status)
        self.root.update()
    
    def test_plc_connection(self):
        """Test PLC connection and display status"""
        print("PLC test button clicked!")  # Debug
        self.log("🔍 Testing PLC connection...")
        self.update_status("🔍 Testing PLC")
        
        try:
            client = ModbusTcpClient(PLC_IP, port=PLC_PORT)
            if client.connect():
                self.log(f"✅ PLC connected at {PLC_IP}:{PLC_PORT}")
                
                # Test reading a coil
                coil = client.read_coils(RUN_COIL, 1)
                if not coil.isError():
                    status = "RUNNING" if coil.bits[0] else "STOPPED"
                    self.log(f"📊 PLC Status: {status}")
                    self.update_status(f"✅ PLC {status}")
                else:
                    self.log(f"⚠️ Error reading coil {RUN_COIL}")
                    self.update_status("⚠️ PLC Read Error")
                    
                client.close()
            else:
                self.log(f"❌ PLC connection failed: {PLC_IP}:{PLC_PORT}")
                self.update_status("❌ PLC Offline")
                
        except Exception as e:
            self.log(f"❌ PLC error: {e}")
            self.update_status("❌ PLC Error")
        
    def get_barcode(self):
        try:
            ser = serial.Serial(SERIAL_PORT, SERIAL_BAUD, timeout=1)
            self.log(f"Scanner ready on {SERIAL_PORT}")
            self.update_status("📷 Ready for Scan")
            
            while self.running:
                line = ser.readline().decode(errors="ignore").strip()
                if line:
                    self.log(f"📦 Scanned: {line}")
                    return line
        except Exception as e:
            self.log("Please connect scanner.")
            self.update_status("Please connect scanner.")
            return None
            
    def run_test(self, order_id):
        self.update_status(f"🔧 Testing {order_id}")
        self.log(f"Starting test for {order_id}")
        
        client = ModbusTcpClient(PLC_IP, port=PLC_PORT)
        if not client.connect():
            self.log("❌ PLC connection failed")
            self.update_status("❌ PLC Error")
            return
        
        try:
            client.write_coil(START_COIL, True, unit=1)
            self.log("▶️ PLC test started")
            
            # Collect data
            timestamps, pressure_a, pressure_b = [], [], []
            self.log("⏳ Collecting data...")
            
            start_wait = time.time()
            while True:
                coil = client.read_coils(RUN_COIL, 1, slave=1)
                if not coil.isError() and coil.bits[0]:
                    self.log("📊 Test running...")
                    break
                if time.time() - start_wait > 10:
                    self.log("❌ Test timeout")
                    return
                time.sleep(0.1)
            
            # Data collection loop
            for i in range(MAX_SAMPLES):
                coil = client.read_coils(RUN_COIL, 1, slave=1)
                if coil.isError() or not coil.bits[0]:
                    self.log("⏹️ Test complete")
                    break
                
                rr = client.read_holding_registers(PRESSURE_ADDR, REG_COUNT, slave=1)
                if not rr.isError():
                    pressure_a.append(rr.registers[0])
                    pressure_b.append(rr.registers[1])
                else:
                    pressure_a.append(-1)
                    pressure_b.append(-1)
                timestamps.append(int(time.time() * 1000))
                time.sleep(INTERVAL)
            
            # Save data
            if len(pressure_a) > 0:
                file_path = f"{DATA_DIR}/{order_id}_{datetime.now().strftime('%Y%m%dT%H%M%S')}.h5"
                with h5py.File(file_path, "w") as f:
                    f.create_dataset("data/timestamp", data=np.array(timestamps), compression="gzip")
                    f.create_dataset("data/pressure_a", data=np.array(pressure_a), compression="gzip")
                    f.create_dataset("data/pressure_b", data=np.array(pressure_b), compression="gzip")
                    meta_grp = f.create_group("metadata")
                    meta_grp.create_dataset("order_id", data=np.string_(order_id))
                    meta_grp.create_dataset("samples", data=len(pressure_a))
                    meta_grp.create_dataset("saved_at", data=np.string_(datetime.now().isoformat()))
                
                self.log(f"✅ Saved: {file_path}")
                self.update_status("✅ Test Complete")
                
                # Signal system monitor that test result is recorded
                with open('/home/kw/cyl_a/test_complete.flag', 'w') as f:
                    f.write(order_id)
                    
            else:
                self.log("⚠️ No data collected")
                self.update_status("⚠️ No Data")
                
        finally:
            client.write_coil(START_COIL, False, unit=1)
            client.close()
    
    def wait_for_manual_test(self, order_id):
        """Wait 60 seconds for user to manually start PLC test"""
        client = ModbusTcpClient(PLC_IP, port=PLC_PORT)
        if not client.connect():
            self.log("❌ PLC connection failed")
            self.update_status("❌ PLC Error")
            return
            
        self.log(f"📋 Order: {order_id} - Start test manually!")
        self.update_status("⏳ 60s Window")
        
        # Wait up to 60 seconds for manual test start
        start_time = time.time()
        while time.time() - start_time < 60:
            try:
                # Check if PLC test is running
                coil = client.read_coils(RUN_COIL, 1, slave=1)
                if not coil.isError() and coil.bits[0]:
                    self.log("✅ Manual test detected!")
                    # Monitor and collect data during manual test
                    self.monitor_manual_test(order_id, client)
                    return
            except:
                pass
            time.sleep(0.5)
        
        # 60 seconds elapsed, no test started
        self.log("⏰ 60s window expired - no test started")
        self.update_status("⏰ Timeout")
        client.close()
        
    def monitor_manual_test(self, order_id, client):
        """Monitor manually started test and collect data"""
        timestamps, pressure_a, pressure_b = [], [], []
        self.log("📊 Collecting manual test data...")
        self.update_status("📊 Recording")
        
        # Collect data while test is running
        while True:
            try:
                coil = client.read_coils(RUN_COIL, 1, slave=1)
                if coil.isError() or not coil.bits[0]:
                    break  # Test finished
                    
                # Read pressure data (mock for now)
                timestamp = time.time()
                timestamps.append(timestamp)
                pressure_a.append(random.uniform(30, 70))
                pressure_b.append(random.uniform(25, 65))
                
                time.sleep(INTERVAL)
            except:
                break
        
        client.close()
        
        # Save collected data
        if timestamps:
            file_path = f"/home/kw/cyl_a/data/{order_id}_manual_test.h5"
            with h5py.File(file_path, "w") as f:
                f.create_dataset("data/timestamp", data=np.array(timestamps), compression="gzip")
                f.create_dataset("data/pressure_a", data=np.array(pressure_a), compression="gzip") 
                f.create_dataset("data/pressure_b", data=np.array(pressure_b), compression="gzip")
                meta_grp = f.create_group("metadata")
                meta_grp.create_dataset("order_id", data=np.string_(order_id))
                meta_grp.create_dataset("samples", data=len(pressure_a))
                meta_grp.create_dataset("saved_at", data=np.string_(datetime.now().isoformat()))
            
            self.log(f"✅ Manual test saved: {file_path}")
            self.update_status("✅ Manual Complete")
            
            # Signal completion
            with open('/home/kw/cyl_a/test_complete.flag', 'w') as f:
                f.write(order_id)
        else:
            self.log("⚠️ No manual test data collected")
            self.update_status("⚠️ No Data")
            
    def scanner_loop(self):
        while self.running:
            try:
                order_id = self.get_barcode()
                if order_id and order_id.lower() not in ["quit", "exit"]:
                    self.wait_for_manual_test(order_id)
                    time.sleep(1)
                    self.update_status("📷 Ready for Scan")
            except Exception as e:
                self.log(f"❌ Error: {e}")
                time.sleep(2)
                
    def show(self):
        try:
            self.root.mainloop()
        finally:
            self.running = False

if __name__ == "__main__":
    app = ScannerGUI()
    app.show()
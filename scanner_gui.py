#!/usr/bin/env python3
import tkinter as tk
from tkinter import scrolledtext
import time
import numpy as np
import h5py
import os
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
            
    def scanner_loop(self):
        while self.running:
            try:
                order_id = self.get_barcode()
                if order_id and order_id.lower() not in ["quit", "exit"]:
                    self.run_test(order_id)
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
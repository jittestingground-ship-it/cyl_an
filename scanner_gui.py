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
        
        # Keep window on top and prevent focus issues
        self.root.attributes('-topmost', True)
        self.root.lift()
        self.root.focus_force()
        
        # Status display
        self.status_label = tk.Label(self.root, text="Scanner Initializing...", 
                                   font=("Arial", 16, "bold"), fg="white", bg='#2c3e50')
        self.status_label.pack(pady=20)
        
        # PLC Status Indicator
        self.plc_frame = tk.Frame(self.root, bg='#2c3e50')
        self.plc_frame.pack(pady=10)
        
        self.plc_status_label = tk.Label(self.plc_frame, text="PLC Status:", 
                                       font=("Arial", 12, "bold"), fg="white", bg='#2c3e50')
        self.plc_status_label.pack(side='left', padx=5)
        
        # Status light (circle)
        self.status_light = tk.Label(self.plc_frame, text="●", font=("Arial", 20), 
                                   fg="gray", bg='#2c3e50')
        self.status_light.pack(side='left', padx=5)
        
        # PLC status text
        self.plc_text = tk.Label(self.plc_frame, text="Checking...", 
                               font=("Arial", 12), fg="white", bg='#2c3e50')
        self.plc_text.pack(side='left', padx=5)
        
        # Activity log
        self.log_text = scrolledtext.ScrolledText(self.root, width=50, height=15,
                                                bg='#34495e', fg='white', font=("Courier", 10))
        self.log_text.pack(pady=10, padx=10, fill='both', expand=True)
        
        self.running = True
        self.log("Scanner GUI Started")
        
        # Start PLC monitoring thread
        self.plc_thread = threading.Thread(target=self.monitor_plc_status, daemon=True)
        self.plc_thread.start()
        
        # Start scanner thread
        self.scanner_thread = threading.Thread(target=self.scanner_loop, daemon=True)
        self.scanner_thread.start()
        
    def log(self, message):
        # Thread-safe GUI update
        self.root.after(0, lambda: self._update_log(message))
        
    def _update_log(self, message):
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        
    def update_status(self, status):
        # Thread-safe GUI update
        self.root.after(0, lambda: self._update_status(status))
        
    def _update_status(self, status):
        self.status_label.config(text=status)
    
    def update_plc_status(self, connected, status_text, error_msg=None):
        """Update PLC status indicator"""
        if connected:
            self.root.after(0, lambda: self.status_light.config(fg="green"))
            self.root.after(0, lambda: self.plc_text.config(text=status_text, fg="lightgreen"))
        else:
            self.root.after(0, lambda: self.status_light.config(fg="red"))
            self.root.after(0, lambda: self.plc_text.config(text=status_text, fg="lightcoral"))
            if error_msg:
                self.log(f"❌ PLC Error: {error_msg}")
    
    def monitor_plc_status(self):
        """Continuously monitor PLC connection status"""
        while self.running:
            try:
                client = ModbusTcpClient(PLC_IP, port=PLC_PORT)
                if client.connect():
                    # Test reading a coil to verify communication
                    coil = client.read_coils(RUN_COIL, 1, slave=1)
                    if not coil.isError():
                        is_running = coil.bits[0]
                        status = "RUNNING" if is_running else "READY"
                        
                        # Try to read pressure values for live display in main status
                        try:
                            rr = client.read_holding_registers(PRESSURE_ADDR, REG_COUNT, slave=1)
                            if not rr.isError():
                                pa, pb = rr.registers[0], rr.registers[1]
                                status_detail = f"{status} | P_A:{pa} P_B:{pb}"
                                # Update main status with live pressure readings
                                self.update_status(f"📊 Live: P_A={pa} P_B={pb} | {status}")
                            else:
                                status_detail = f"{status} | Pressure: N/A"
                                self.update_status(f"📷 Ready for Scan | {status}")
                        except:
                            status_detail = status
                            self.update_status(f"📷 Ready for Scan | {status}")
                            
                        self.update_plc_status(True, status_detail)
                        # Don't print debug info since status is now in main display
                    else:
                        self.update_plc_status(False, "Read Error", "Cannot read coil data")
                        self.update_status("❌ PLC Read Error")
                    client.close()
                else:
                    self.update_plc_status(False, "Disconnected", f"Cannot connect to {PLC_IP}:{PLC_PORT}")
                    self.update_status("❌ PLC Disconnected")
                    
            except Exception as e:
                self.update_plc_status(False, "Error", str(e))
                self.update_status("❌ PLC Error")
                
            time.sleep(2)  # Check every 2 seconds for more responsive updates
        
    def get_barcode(self):
        try:
            ser = serial.Serial(SERIAL_PORT, SERIAL_BAUD, timeout=0.1)  # Short timeout
            self.log(f"Scanner ready on {SERIAL_PORT}")
            self.update_status("📷 Ready for Scan")
            
            while self.running:
                line = ser.readline().decode(errors="ignore").strip()
                if line:
                    self.log(f"📦 Scanned: {line}")
                    ser.close()
                    return line
                time.sleep(0.1)  # Small delay to prevent CPU spinning
        except Exception as e:
            self.log("Please connect scanner.")
            self.update_status("Please connect scanner.")
            time.sleep(2)  # Wait before retrying
            return None
            
    def run_test(self, order_id):
        self.update_status(f"🔧 Initializing Test: {order_id}")
        self.log(f"Starting test for {order_id}")
        
        client = ModbusTcpClient(PLC_IP, port=PLC_PORT)
        if not client.connect():
            self.log("❌ PLC connection failed")
            self.update_status("❌ PLC Error")
            return
        
        try:
            self.update_status("🚀 Starting PLC Test Sequence")
            client.write_coil(START_COIL, True, slave=1)
            self.log("▶️ PLC test started")
            
            # Collect data
            timestamps, pressure_a, pressure_b = [], [], []
            self.update_status("⏳ Waiting for PLC Response...")
            
            start_wait = time.time()
            while True:
                coil = client.read_coils(RUN_COIL, 1, slave=1)
                if not coil.isError() and coil.bits[0]:
                    self.update_status("✅ PLC Active - Test Running")
                    self.log("📊 Test running...")
                    break
                if time.time() - start_wait > 60:  # Wait up to 60 seconds for C1 coil activation
                    self.log("❌ Test timeout - C1 coil did not activate within 60 seconds")
                    self.update_status("❌ PLC Timeout")
                    return
                # Show remaining wait time
                elapsed = time.time() - start_wait
                remaining = 60 - elapsed
                self.update_status(f"⏳ Waiting for C1 coil... {remaining:.0f}s remaining")
                time.sleep(0.5)
            
            # Data collection loop with live updates
            sample_count = 0
            last_update_time = time.time()
            test_start_time = time.time()  # Record when test data collection starts
            
            for i in range(MAX_SAMPLES):
                coil = client.read_coils(RUN_COIL, 1, slave=1)
                if coil.isError() or not coil.bits[0]:
                    self.update_status("⏹️ Test Sequence Complete")
                    self.log("⏹️ Test complete")
                    break
                
                rr = client.read_holding_registers(PRESSURE_ADDR, REG_COUNT, slave=1)
                if not rr.isError():
                    pressure_a.append(rr.registers[0])
                    pressure_b.append(rr.registers[1])
                    sample_count += 1
                    
                    # Live status updates every 0.5 seconds
                    if time.time() - last_update_time > 0.5:
                        pa_val = rr.registers[0]
                        pb_val = rr.registers[1] 
                        elapsed_time = time.time() - test_start_time
                        self.update_status(f"📊 Testing: P_A={pa_val} P_B={pb_val} [{sample_count} samples] {elapsed_time:.1f}s")
                        last_update_time = time.time()
                else:
                    pressure_a.append(-1)
                    pressure_b.append(-1)
                    self.update_status(f"⚠️ Read Error - Sample {sample_count}")
                    
                # Store timestamp as seconds from test start (0, 0.01, 0.02, etc.)
                elapsed_seconds = time.time() - test_start_time
                timestamps.append(elapsed_seconds)
                time.sleep(INTERVAL)
            
            # Save data with live feedback
            if len(pressure_a) > 0:
                self.update_status(f"💾 Saving {len(pressure_a)} samples...")
                file_path = f"{DATA_DIR}/{order_id}_{datetime.now().strftime('%Y%m%dT%H%M%S')}.h5"
                
                with h5py.File(file_path, "w") as f:
                    self.update_status("💾 Writing timestamp data...")
                    f.create_dataset("data/timestamp", data=np.array(timestamps), compression="gzip")
                    
                    self.update_status("💾 Writing pressure A data...")
                    f.create_dataset("data/pressure_a", data=np.array(pressure_a), compression="gzip")
                    
                    self.update_status("💾 Writing pressure B data...")
                    f.create_dataset("data/pressure_b", data=np.array(pressure_b), compression="gzip")
                    
                    self.update_status("💾 Writing metadata...")
                    meta_grp = f.create_group("metadata")
                    meta_grp.create_dataset("order_id", data=order_id.encode('utf-8'))
                    meta_grp.create_dataset("samples", data=len(pressure_a))
                    meta_grp.create_dataset("saved_at", data=datetime.now().isoformat().encode('utf-8'))
                    # Store actual timestamp for metadata (not the 0-based test timestamps)
                    meta_grp.create_dataset("test_started_at", data=int(test_start_time * 1000))  # Original timestamp in ms
                
                self.log(f"✅ Saved: {file_path} ({len(pressure_a)} samples)")
                self.update_status(f"✅ Complete: {order_id} - {len(pressure_a)} samples saved")
                
                # Signal system monitor that test result is recorded
                with open('/home/kw/cyl_a/test_complete.flag', 'w') as f:
                    f.write(order_id)
                    
            else:
                self.log("⚠️ No data collected")
                self.update_status("⚠️ No Data - Test Failed")
                
        finally:
            client.write_coil(START_COIL, False, slave=1)
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
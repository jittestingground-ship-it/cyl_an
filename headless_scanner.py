#!/usr/bin/env python3
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

class HeadlessScanner:
    def __init__(self):
        self.running = True
        print("🚀 Headless Scanner Started")
        print("📍 Commands: 'test' = test PLC, 'quit' = exit")
        
    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")
        
    def test_plc_connection(self):
        """Test PLC connection and display status"""
        self.log("🔍 Testing PLC connection...")
        
        try:
            client = ModbusTcpClient(PLC_IP, port=PLC_PORT)
            if client.connect():
                self.log(f"✅ PLC connected at {PLC_IP}:{PLC_PORT}")
                
                # Test reading a coil
                coil = client.read_coils(RUN_COIL)
                if not coil.isError():
                    status = "RUNNING" if coil.bits[0] else "STOPPED"
                    self.log(f"📊 PLC Status: {status}")
                else:
                    self.log(f"⚠️ Error reading coil {RUN_COIL}")
                    
                client.close()
                return True
            else:
                self.log(f"❌ PLC connection failed: {PLC_IP}:{PLC_PORT}")
                return False
                
        except Exception as e:
            self.log(f"❌ PLC error: {e}")
            return False
        
    def get_barcode(self):
        try:
            ser = serial.Serial(SERIAL_PORT, SERIAL_BAUD, timeout=0.1)
            self.log("JIT Test Stand")
            
            while self.running:
                line = ser.readline().decode(errors="ignore").strip()
                if line:
                    self.log(f"📦 Scanned: {line}")
                    ser.close()
                    return line
                time.sleep(0.1)
        except Exception as e:
            self.log("⚠️ Please connect scanner")
            time.sleep(2)
            return None
            
    def run_test(self, order_id):
        self.log(f"🔧 Starting test for {order_id}")
        
        client = ModbusTcpClient(PLC_IP, port=PLC_PORT)
        if not client.connect():
            self.log("❌ PLC connection failed")
            return
        
        try:
            client.write_coil(START_COIL, True)
            self.log("▶️ PLC test started")
            
            # Collect data
            timestamps, pressure_a, pressure_b = [], [], []
            self.log("⏳ Collecting data...")
            
            start_wait = time.time()
            while True:
                coil = client.read_coils(RUN_COIL)
                if not coil.isError() and coil.bits[0]:
                    self.log("📊 Test running...")
                    break
                if time.time() - start_wait > 10:
                    self.log("❌ Test timeout")
                    return
                time.sleep(0.1)
            
            # Data collection loop
            for i in range(MAX_SAMPLES):
                coil = client.read_coils(RUN_COIL)
                if coil.isError() or not coil.bits[0]:
                    self.log("⏹️ Test complete")
                    break
                
                rr = client.read_holding_registers(PRESSURE_ADDR, REG_COUNT)
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
                
                # Signal completion
                with open('/home/kw/cyl_a/test_complete.flag', 'w') as f:
                    f.write(order_id)
                    
            else:
                self.log("⚠️ No data collected")
                
        finally:
            client.write_coil(START_COIL, False)
            client.close()
            
    def run(self):
        """Main loop - scan barcodes and run tests"""
        self.log("JIT Test Stand")
        while self.running:
            try:
                # Check for barcode scan
                order_id = self.get_barcode()
                if order_id:
                    if order_id.lower() == "quit":
                        break
                    elif order_id.lower() == "test":
                        self.test_plc_connection()
                    else:
                        self.run_test(order_id)
                time.sleep(0.1)
            except KeyboardInterrupt:
                self.log("🛑 Shutting down...")
                break
            except Exception as e:
                self.log(f"❌ Error: {e}")
                time.sleep(2)
        self.running = False
        self.log("👋 Scanner stopped")

if __name__ == "__main__":
    scanner = HeadlessScanner()
    scanner.run()
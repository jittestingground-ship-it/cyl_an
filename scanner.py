#!/usr/bin/env python3
import time
import numpy as np
import h5py
import os
from datetime import datetime
from pymodbus.client import ModbusTcpClient
import serial

# Find external drive (use existing discovery system)
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
SET_PRESSURE = 9
TEST_TIME = 13
CYCLE_COUNT = 16
MAX_LEAK_PRESSURE = 38
TEST_PASS_FAIL = 49
DELTA_A_AVG = 51
DELTA_B_AVG = 52

def get_barcode():
    ser = serial.Serial(SERIAL_PORT, SERIAL_BAUD, timeout=1)
    print(f"📷 Scanner ready on {SERIAL_PORT}")
    while True:
        line = ser.readline().decode(errors="ignore").strip()
        if line:
            print(f"📦 Scanned: {line}")
            return line

def collect_from_plc(client, order_id):
    timestamps, pressure_a, pressure_b = [], [], []
    print("⏳ Waiting for test start...")
    
    start_wait = time.time()
    while True:
        coil = client.read_coils(RUN_COIL, 1, slave=1)
        if not coil.isError() and coil.bits[0]:
            print("▶️ Test running, collecting data...")
            break
        if time.time() - start_wait > 10:
            print("❌ Test timeout")
            return np.array([]), np.array([]), np.array([]), {}
        time.sleep(0.1)
    
    # Collect data while test runs
    for _ in range(MAX_SAMPLES):
        coil = client.read_coils(RUN_COIL, 1, slave=1)
        if coil.isError() or not coil.bits[0]:
            print("⏹️ Test complete")
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
    
    # Get metadata
    metadata = {"order_id": order_id, "samples": len(pressure_a), "saved_at": datetime.now().isoformat()}
    return np.array(timestamps), np.array(pressure_a), np.array(pressure_b), metadata

def save_to_hdf5(order_id, timestamps, pressure_a, pressure_b, metadata):
    file_path = f"{DATA_DIR}/{order_id}_{datetime.now().strftime('%Y%m%dT%H%M%S')}.h5"
    with h5py.File(file_path, "w") as f:
        f.create_dataset("data/timestamp", data=timestamps, compression="gzip")
        f.create_dataset("data/pressure_a", data=pressure_a, compression="gzip")
        f.create_dataset("data/pressure_b", data=pressure_b, compression="gzip")
        meta_grp = f.create_group("metadata")
        for key, value in metadata.items():
            meta_grp.create_dataset(key, data=np.string_(str(value)))
    print(f"✅ Saved: {file_path}")

def run_test(order_id):
    client = ModbusTcpClient(PLC_IP, port=PLC_PORT)
    if not client.connect():
        print("❌ PLC connection failed")
        return
    
    try:
        client.write_coil(START_COIL, True, unit=1)
        print(f"▶️ Started test for {order_id}")
        ts, a, b, metadata = collect_from_plc(client, order_id)
        if len(a) > 0:
            save_to_hdf5(order_id, ts, a, b, metadata)
        else:
            print("⚠️ No data collected")
    finally:
        client.write_coil(START_COIL, False, unit=1)
        client.close()

if __name__ == "__main__":
    print("🔍 Scanner System Ready")
    while True:
        order_id = get_barcode()
        if order_id.lower() in ["quit", "exit"]:
            break
        run_test(order_id)
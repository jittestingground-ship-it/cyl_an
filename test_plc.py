#!/usr/bin/env python3
from pymodbus.client import ModbusTcpClient

PLC_IP = "192.168.0.11"
PLC_PORT = 502
RUN_COIL = 16384

print(f"Testing PLC connection to {PLC_IP}:{PLC_PORT}")

try:
    client = ModbusTcpClient(PLC_IP, port=PLC_PORT)
    if client.connect():
        print("✅ PLC connected successfully!")
        
        # Test reading a coil
        coil = client.read_coils(RUN_COIL, 1)
        if not coil.isError():
            status = "RUNNING" if coil.bits[0] else "STOPPED"
            print(f"📊 PLC Status: {status}")
        else:
            print(f"⚠️ Error reading coil {RUN_COIL}")
            
        client.close()
    else:
        print("❌ PLC connection failed")
        
except Exception as e:
    print(f"❌ Error: {e}")
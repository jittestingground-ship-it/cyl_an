#!/usr/bin/env python3
import socket
from pymodbus.client import ModbusTcpClient

# Found devices from ARP table
test_ips = ["192.168.0.11", "192.168.1.12", "192.168.1.22", "192.168.1.8"]

def test_modbus_connection(ip):
    print(f"\nTesting {ip}:502...")
    
    # First test basic socket connection
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((ip, 502))
        sock.close()
        
        if result == 0:
            print(f"  ✅ Port 502 is open on {ip}")
            
            # Try Modbus connection
            client = ModbusTcpClient(ip, port=502)
            if client.connect():
                print(f"  ✅ Modbus connection successful to {ip}")
                client.close()
                return ip
            else:
                print(f"  ⚠️ Port open but Modbus failed on {ip}")
        else:
            print(f"  ❌ Port 502 closed on {ip}")
            
    except Exception as e:
        print(f"  ❌ Error testing {ip}: {e}")
    
    return None

print("Scanning for PLC with Modbus port 502...")
for ip in test_ips:
    plc_ip = test_modbus_connection(ip)
    if plc_ip:
        print(f"\n🎯 FOUND PLC at {plc_ip}!")
        break
else:
    print("\n❌ No PLC found on any tested IP addresses")
    print("The PLC might be:")
    print("1. On a different IP address")
    print("2. Not powered on")
    print("3. On a different network subnet")
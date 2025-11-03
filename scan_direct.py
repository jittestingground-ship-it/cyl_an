#!/usr/bin/env python3
import subprocess
import socket

def scan_direct_subnet():
    """Scan 192.168.0.x subnet for any devices"""
    print("🔍 Scanning 192.168.0.x subnet for PLC...")
    
    found_devices = []
    
    for i in range(1, 255):
        ip = f"192.168.0.{i}"
        
        # Quick ping test
        try:
            result = subprocess.run(['ping', '-c', '1', '-W', '1', ip], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(f"  ✅ Device found: {ip}")
                found_devices.append(ip)
                
                # Test Modbus port
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                modbus_result = sock.connect_ex((ip, 502))
                sock.close()
                
                if modbus_result == 0:
                    print(f"    🎯 Modbus port 502 OPEN on {ip}!")
                else:
                    print(f"    ⚠️ No Modbus on {ip}")
                    
        except:
            pass
    
    return found_devices

devices = scan_direct_subnet()

if not devices:
    print("\n❌ No devices found on 192.168.0.x network")
    print("\n💡 Troubleshooting steps:")
    print("1. Check PLC power - is it turned on?")
    print("2. Check Ethernet cable connection")
    print("3. Check PLC network configuration:")
    print("   - PLC IP should be 192.168.1.11")
    print("   - Subnet mask: 255.255.255.0") 
    print("   - Gateway: 192.168.0.10 (this Pi)")
    print("4. Some PLCs need crossover cable for direct connection")
    print("5. Check PLC manual for default IP address")
else:
    print(f"\n✅ Found {len(devices)} device(s) on direct connection")
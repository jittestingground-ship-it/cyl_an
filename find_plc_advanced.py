#!/usr/bin/env python3
import subprocess
import socket
from pymodbus.client import ModbusTcpClient

def scan_subnet_for_plc():
    """Scan all possible IP addresses in common subnets for PLCs"""
    
    # Common PLC IP ranges
    subnets = [
        "192.168.1.",   # Current network
        "192.168.0.",   # Original PLC config  
        "192.168.2.",   # Common alternative
        "10.0.0.",      # Another common range
        "172.16.0."     # Industrial networks
    ]
    
    print("🔍 Scanning for PLC with Modbus port 502...")
    print("This may take a few minutes...\n")
    
    found_devices = []
    
    for subnet in subnets:
        print(f"Scanning {subnet}x subnet...")
        
        # Scan first 20 addresses in each subnet (most common range)
        for i in range(1, 21):
            ip = f"{subnet}{i}"
            
            try:
                # Quick socket test first
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.5)  # Very quick timeout
                result = sock.connect_ex((ip, 502))
                sock.close()
                
                if result == 0:
                    print(f"  ✅ Found Modbus port open: {ip}")
                    
                    # Test actual Modbus communication
                    client = ModbusTcpClient(ip, port=502)
                    if client.connect():
                        print(f"  🎯 CONFIRMED PLC at {ip}!")
                        found_devices.append(ip)
                        client.close()
                    
            except:
                pass  # Skip unreachable IPs silently
    
    return found_devices

# Alternative method: Check DHCP lease table
def check_dhcp_leases():
    """Check router's DHCP table for devices"""
    print("\n📋 Checking for known network devices...")
    
    try:
        # Show current ARP table
        result = subprocess.run(['arp', '-a'], capture_output=True, text=True)
        print("Known devices on network:")
        print(result.stdout)
        
        print("\nTip: Check your router's web interface at http://192.168.1.1")
        print("Look for 'DHCP Client List' or 'Connected Devices'")
        print("PLCs often show up with names like 'PLC', 'Modicon', 'Allen-Bradley', etc.")
        
    except Exception as e:
        print(f"Error checking network: {e}")

if __name__ == "__main__":
    # Method 1: Network scan
    plcs = scan_subnet_for_plc()
    
    if plcs:
        print(f"\n🎯 Found {len(plcs)} PLC(s):")
        for plc in plcs:
            print(f"  - {plc}")
    else:
        print("\n❌ No PLCs found in scan")
        
        # Method 2: Show network info
        check_dhcp_leases()
        
        print("\n💡 Other ways to find PLC IP:")
        print("1. Check PLC display panel/HMI for network settings")
        print("2. Use PLC programming software to scan network")
        print("3. Check router admin panel for connected devices")
        print("4. Look for PLC manufacturer's network discovery tool")
        print("5. Check if PLC has a default IP (often 192.168.1.100)")
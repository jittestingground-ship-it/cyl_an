#!/usr/bin/env python3
import socket

# Common PLC/Modbus ports to test
ports_to_test = [
    (502, "Modbus TCP (standard)"),
    (503, "Modbus TCP (alternative)"),
    (102, "Siemens S7"),
    (44818, "Ethernet/IP"),
    (2222, "EtherNet/IP explicit"),
    (1962, "PCWorx"),
    (9600, "Custom Modbus"),
    (20000, "DNP3"),
    (80, "HTTP/Web interface"),
    (23, "Telnet"),
    (21, "FTP")
]

def test_port(ip, port, description):
    """Test if a specific port is open on an IP"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((ip, port))
        sock.close()
        
        if result == 0:
            return True
        return False
    except:
        return False

def scan_ports_on_ip(ip):
    """Scan all common PLC ports on a specific IP"""
    print(f"\n🔍 Testing ports on {ip}:")
    open_ports = []
    
    for port, description in ports_to_test:
        if test_port(ip, port, description):
            print(f"  ✅ Port {port} OPEN - {description}")
            open_ports.append((port, description))
        else:
            print(f"  ❌ Port {port} closed - {description}")
    
    return open_ports

# Test the original PLC IP
print("Testing original PLC IP: 192.168.1.11")
scan_ports_on_ip("192.168.1.11")

# Test some devices we found on current network
test_ips = ["192.168.1.12", "192.168.1.22", "192.168.1.8"]

for ip in test_ips:
    open_ports = scan_ports_on_ip(ip)
    if open_ports:
        print(f"  🎯 Found {len(open_ports)} open ports on {ip}")

print(f"\n📝 Current configuration:")
print(f"  PLC_IP = 192.168.1.11")
print(f"  PLC_PORT = 502")
print(f"\nPort 502 is the STANDARD Modbus TCP port.")
print(f"If your PLC uses a different port, we need to update PLC_PORT in the code.")
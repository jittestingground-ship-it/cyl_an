# Stub for PLC communication using pymodbus
from pymodbus.client.sync import ModbusTcpClient

def read_pressure_from_plc(ip, port=502):
    client = ModbusTcpClient(ip, port)
    client.connect()
    # Example: Read holding register at 0 (actual PLC setup may differ)
    rr = client.read_holding_registers(0, 2)
    pressure_a, pressure_b = rr.registers
    client.close()
    return pressure_a, pressure_b

# For demo/testing:
if __name__ == "__main__":
    print(read_pressure_from_plc("192.168.0.100"))
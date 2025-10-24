from pymodbus.client import ModbusTcpClient

PLC_IP = "192.168.0.11"
PLC_PORT = 502
RUN_COIL = 16384

if __name__ == "__main__":
    print(f"Connecting to PLC at {PLC_IP}:{PLC_PORT} ...")
    client = ModbusTcpClient(PLC_IP, port=PLC_PORT)
    if client.connect():
        print("✅ Connected!")
        coil = client.read_coils(RUN_COIL, 1)
        if not coil.isError():
            print(f"Coil {RUN_COIL} value: {coil.bits[0]}")
        else:
            print(f"❌ Error reading coil {RUN_COIL}: {coil}")
        client.close()
    else:
        print("❌ Could not connect to PLC.")

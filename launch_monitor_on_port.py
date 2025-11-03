import socket
import time
import subprocess

# Wait for port 5000 to be open, then launch system monitor
PORT = 5000
MONITOR_CMD = ['/home/kw/cyl_a/venv/bin/python', '/home/kw/cyl_a/system_monitor_qt.py']

while True:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if s.connect_ex(('localhost', PORT)) == 0:
            subprocess.Popen(MONITOR_CMD)
            break
    time.sleep(2)

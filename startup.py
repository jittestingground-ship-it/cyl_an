#!/usr/bin/env python3
import subprocess
import time
import os

# Set display for headless mode if not already set
if 'DISPLAY' not in os.environ:
    os.environ['DISPLAY'] = ':1'

# Change to script directory
os.chdir('/home/kw/cyl_a')

# Start Excel data receiver on port 5000
subprocess.Popen(['./venv/bin/python', 'excel_receiver.py'])

# Start system monitor - it will handle the rest
subprocess.Popen(['python3', 'system_monitor.py'])
#!/usr/bin/env python3
import subprocess
import os
import time

def setup_virtual_display():
    """Set up virtual display for headless operation"""
    try:
        # Check if Xvfb is installed
        subprocess.run(['which', 'Xvfb'], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        print("Installing Xvfb...")
        subprocess.run(['sudo', 'apt', 'update'], check=False)
        subprocess.run(['sudo', 'apt', 'install', '-y', 'xvfb'], check=False)
    
    # Start virtual display
    print("Starting virtual display...")
    xvfb_process = subprocess.Popen([
        'Xvfb', ':1', '-screen', '0', '1024x768x24'
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Set display environment variable
    os.environ['DISPLAY'] = ':1'
    
    time.sleep(2)  # Wait for Xvfb to start
    print("Scanner Running display ready on :1")
    return xvfb_process

if __name__ == "__main__":
    xvfb_process = setup_virtual_display()
    
    # Start main application
    try:
        subprocess.run(['python3', '/home/kw/cyl_a/startup.py'])
    finally:
        # Clean up
        if xvfb_process:
            xvfb_process.terminate()
            print("Virtual display stopped")
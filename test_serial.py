#!/usr/bin/env python3
import tkinter as tk
import threading
import time
import serial

class SerialTest:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Serial Test")
        self.root.geometry("300x200")
        
        self.label = tk.Label(self.root, text="Serial Test", font=("Arial", 14))
        self.label.pack(pady=20)
        
        self.button = tk.Button(self.root, text="Test Button", command=self.button_clicked,
                               font=("Arial", 12), bg='red', fg='white', width=15, height=2)
        self.button.pack(pady=20)
        
        self.running = True
        
        # Start serial thread
        self.thread = threading.Thread(target=self.serial_task, daemon=True)
        self.thread.start()
        
    def button_clicked(self):
        print("Serial test button clicked!")
        self.label.config(text="Button Works with Serial!")
        
    def serial_task(self):
        while self.running:
            try:
                print("Trying to open serial port...")
                ser = serial.Serial("/dev/ttyUSB0", 9600, timeout=0.1)
                print("Serial port opened!")
                ser.close()
            except Exception as e:
                print(f"Serial error (expected): {e}")
            time.sleep(2)
            
    def show(self):
        try:
            self.root.mainloop()
        finally:
            self.running = False

if __name__ == "__main__":
    print("Starting serial test...")
    app = SerialTest()
    app.show()
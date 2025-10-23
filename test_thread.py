#!/usr/bin/env python3
import tkinter as tk
import threading
import time

class ThreadTest:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Thread Test")
        self.root.geometry("300x200")
        
        self.label = tk.Label(self.root, text="Thread Test", font=("Arial", 14))
        self.label.pack(pady=20)
        
        self.button = tk.Button(self.root, text="Test Button", command=self.button_clicked,
                               font=("Arial", 12), bg='green', fg='white', width=15, height=2)
        self.button.pack(pady=20)
        
        self.running = True
        
        # Start background thread
        self.thread = threading.Thread(target=self.background_task, daemon=True)
        self.thread.start()
        
    def button_clicked(self):
        print("Thread test button clicked!")
        self.label.config(text="Button Works with Thread!")
        
    def background_task(self):
        count = 0
        while self.running:
            print(f"Background task running: {count}")
            time.sleep(2)
            count += 1
            
    def show(self):
        try:
            self.root.mainloop()
        finally:
            self.running = False

if __name__ == "__main__":
    print("Starting thread test...")
    app = ThreadTest()
    app.show()
import tkinter as tk
import subprocess
import time
import os

PROCESS_LABELS = [
    "Excel Host Ready",
    "Virtual Environment Started",
    "Dashboard Running",
    "Scanner Ready",
    "Testing",
    "Test Result Recorded",
    "Dashboard Updated",
    "Building Email",
    "Email Sent"
]

class SystemMonitor:
    def __init__(self, width=250, height=420):
        self.root = tk.Tk()
        self.root.title("System Monitor")
        self.root.geometry(f"{width}x{height}+50+200")  # Centered height
        self.root.configure(bg='#e5e5e5')
        self.frame = tk.Frame(self.root, bg='#e5e5e5')
        self.frame.pack(fill='both', expand=True)
        self.labels = []
        self.dots = []
        self.status = [False] * len(PROCESS_LABELS)
        self.processes = []
        self.startup_step = 0
        self.startup_time = time.time()
        for i, label_text in enumerate(PROCESS_LABELS):
            lab = tk.Label(self.frame, text=label_text, font=("Arial", 8, "bold"), fg="#000042",
                           bg='#e5e5e5', anchor="center", wraplength=120, relief="solid", bd=1)
            lab.grid(row=i, column=0, sticky="nsew", padx=2, pady=2)
            
            dot_frame = tk.Frame(self.frame, bg='#e5e5e5', relief="solid", bd=1)
            dot_frame.grid(row=i, column=1, sticky="nsew", padx=2, pady=2)
            dot = tk.Canvas(dot_frame, width=20, height=20, bg='#e5e5e5', highlightthickness=0)
            dot.create_oval(6, 6, 14, 14, fill="#cccccc", tags="circle")
            dot.pack(expand=True)
            
            self.labels.append(lab)
            self.dots.append(dot)
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_columnconfigure(1, weight=1)
        for i in range(len(PROCESS_LABELS)):
            self.frame.grid_rowconfigure(i, weight=1)
        self.root.after(2000, self._refresh)

    def mark_complete(self, index):
        """Turn dot green for process at index."""
        if 0 <= index < len(self.dots):
            self.dots[index].itemconfig("circle", fill="green")
            self.status[index] = True

    def _refresh(self):
        current_time = time.time()
        elapsed = current_time - self.startup_time
        
        # Check for test completion flag
        if os.path.exists('/home/kw/cyl_a/test_complete.flag'):
            if not self.status[5]:  # Test Result Recorded not yet marked
                self.mark_complete(5)
                os.remove('/home/kw/cyl_a/test_complete.flag')
        
        # Startup sequence with delays
        if self.startup_step == 0 and elapsed > 2:  # Excel Host Ready
            self.mark_complete(0)
            self.startup_step = 1
        elif self.startup_step == 1 and elapsed > 4:  # Virtual Environment Started
            self.mark_complete(1)
            self.startup_step = 2
        elif self.startup_step == 2 and elapsed > 6:  # Dashboard Running
            try:
                p = subprocess.Popen(['./venv/bin/python', 'autoproto.py'], cwd='/home/kw/cyl_a')
                self.processes.append(p)
                self.mark_complete(2)
            except:
                pass
            self.startup_step = 3
        elif self.startup_step == 3 and elapsed > 8:  # Scanner Ready
            try:
                p = subprocess.Popen(['./venv/bin/python', 'scanner_gui.py'], cwd='/home/kw/cyl_a')
                self.processes.append(p)
                self.mark_complete(3)
            except:
                pass
            self.startup_step = 4
        elif self.startup_step == 4 and elapsed > 10:  # Testing - removed auto trigger
            # Testing only activates when barcode is scanned
            self.startup_step = 5
            
        self.root.after(2000, self._refresh)

    def show(self):
        self.root.mainloop()

# DEMO: Standalone usage
if __name__ == "__main__":
    monitor = SystemMonitor()
    monitor.show()

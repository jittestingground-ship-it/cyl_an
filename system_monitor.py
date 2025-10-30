import tkinter as tk
import subprocess
import time
import os

PROCESS_LABELS = [
    "Excel Host Ready",
    "Virtual Environment Started",
    "Dashboard Running",
    "Scanner Running",
    "Testing",
    "Test Result Recorded",
    "Dashboard Updated",
    "Building Email",
    "Email ON/OFF",
    "Email Sent"
]

class SystemMonitor:
    def __init__(self, width=250, height=460):
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
        self.email_on = False
        for i, label_text in enumerate(PROCESS_LABELS):
            lab = tk.Label(self.frame, text=label_text, font=("Arial", 8, "bold"), fg="#000042",
                           bg='#e5e5e5', anchor="center", wraplength=120, relief="solid", bd=1)
            lab.grid(row=i, column=0, sticky="nsew", padx=2, pady=2)

            dot_frame = tk.Frame(self.frame, bg='#e5e5e5', relief="solid", bd=1)
            dot_frame.grid(row=i, column=1, sticky="nsew", padx=2, pady=2)
            dot = tk.Canvas(dot_frame, width=20, height=20, bg='#e5e5e5', highlightthickness=0)
            if label_text == "Email ON/OFF":
                dot.create_oval(6, 6, 14, 14, fill="red", tags="circle")
            else:
                dot.create_oval(6, 6, 14, 14, fill="#cccccc", tags="circle")
            dot.pack(expand=True)

            self.labels.append(lab)
            self.dots.append(dot)
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_columnconfigure(1, weight=1)
        for i in range(len(PROCESS_LABELS)):
            self.frame.grid_rowconfigure(i, weight=1)

        # Add Email ON/OFF button below the columns
        self.email_btn = tk.Button(self.root, text="Email ON / OFF", command=self.toggle_email, font=("Arial", 10, "bold"), bg="#dddddd")
        self.email_btn.pack(pady=8)

        self.root.after(2000, self._refresh)

    def toggle_email(self):
        # Toggle the email_on state and update the dot color
        self.email_on = not self.email_on
        idx = PROCESS_LABELS.index("Email ON/OFF")
        color = "green" if self.email_on else "red"
        self.dots[idx].itemconfig("circle", fill=color)

    def mark_complete(self, index):
        """Turn dot green for process at index (except Email ON/OFF, which is controlled by toggle)."""
        if 0 <= index < len(self.dots):
            if PROCESS_LABELS[index] == "Email ON/OFF":
                # Don't auto-mark, handled by toggle
                return
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
        # Step 0: Excel Host Ready
        if self.startup_step == 0 and elapsed > 2:
            self.mark_complete(0)
            self.startup_step = 1

        # Step 1: Virtual Environment Started (only after Excel receiver is running and monitor is up)
        elif self.startup_step == 1:
            # Check if Excel receiver is running on port 5000
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', 5000))
            sock.close()
            if result == 0:
                # Excel receiver is running, now start venv Python (autoproto.py)
                import psutil
                venv_python = '/home/kw/cyl_a/venv/bin/python'
                found_venv = False
                for proc in psutil.process_iter(['exe', 'cmdline']):
                    try:
                        if proc.info['exe'] and proc.info['exe'].endswith('python') and proc.info['exe'] == venv_python:
                            found_venv = True
                            break
                    except Exception:
                        continue
                idx = PROCESS_LABELS.index("Virtual Environment Started")
                if not found_venv:
                    try:
                        p = subprocess.Popen([venv_python, 'autoproto.py'], cwd='/home/kw/cyl_a')
                        self.processes.append(p)
                    except:
                        pass
                # Check again for venv python process
                found_venv = False
                for proc in psutil.process_iter(['exe', 'cmdline']):
                    try:
                        if proc.info['exe'] and proc.info['exe'].endswith('python') and proc.info['exe'] == venv_python:
                            found_venv = True
                            break
                    except Exception:
                        continue
                if found_venv:
                    self.dots[idx].itemconfig("circle", fill="green")
                    self.status[idx] = True
                    self.startup_step = 2
                elif elapsed > 8:
                    self.dots[idx].itemconfig("circle", fill="red")
                    self.status[idx] = False
                    self.startup_step = 2
            else:
                # Excel receiver not running yet, keep dot transparent/gray
                idx = PROCESS_LABELS.index("Virtual Environment Started")
                self.dots[idx].itemconfig("circle", fill="#cccccc")

        # Step 2: Dashboard Running
        elif self.startup_step == 2 and elapsed > 10:
            self.mark_complete(2)
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

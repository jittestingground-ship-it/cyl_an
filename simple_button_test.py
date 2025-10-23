#!/usr/bin/env python3
import tkinter as tk

def button_test():
    print("✅ Button clicked successfully!")
    label.config(text="Button Works!")
    # Keep window on top after button click
    root.lift()
    root.attributes('-topmost', True)

root = tk.Tk()
root.title("Simple Button Test")
root.geometry("300x150")

# Keep window on top
root.attributes('-topmost', True)
root.lift()
root.focus_force()

label = tk.Label(root, text="Click to test", font=("Arial", 14))
label.pack(pady=20)

button = tk.Button(root, text="Click Me", command=button_test,
                   font=("Arial", 12), bg='green', fg='white', width=15, height=2)
button.pack(pady=20)

print("Simple button test starting...")
root.mainloop()
print("Button test ended")
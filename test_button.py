#!/usr/bin/env python3
import tkinter as tk

def button_clicked():
    print("Button clicked!")
    label.config(text="Button Works!")

root = tk.Tk()
root.title("Button Test")
root.geometry("300x200")

label = tk.Label(root, text="Click the button", font=("Arial", 14))
label.pack(pady=20)

button = tk.Button(root, text="Test Button", command=button_clicked, 
                   font=("Arial", 12), bg='blue', fg='white', width=15, height=2)
button.pack(pady=20)

print("Starting simple button test...")
root.mainloop()
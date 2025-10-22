#!/usr/bin/env python3
import tkinter as tk

def test_button_click():
    print("Button clicked!")
    label.config(text="Button was clicked!")

root = tk.Tk()
root.title("Button Test")
root.geometry("300x200")

label = tk.Label(root, text="Click the button below")
label.pack(pady=20)

button = tk.Button(root, text="Test Button", 
                  command=test_button_click,
                  bg='#3498db', fg='white',
                  width=20, height=2)
button.pack(pady=20)

print("Starting button test GUI...")
root.mainloop()
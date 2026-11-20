import tkinter as tk
from tkinter import ttk

root = tk.Tk()
root.title("Font Test")

shared_font = ("Helvetica", 12)

classic = tk.Frame(root, relief=tk.SOLID, borderwidth=1)
classic.pack(side=tk.LEFT, padx=20, pady=10)

label = tk.Label(classic, text="Classic tk.Frame", font=shared_font)
label.pack(padx=5, pady=5)

modern = ttk.Frame(root, relief=tk.SOLID, borderwidth=1)
modern.pack(side=tk.LEFT, padx=20, pady=10)

label2 = tk.Label(modern, text="Themed ttk.Frame", font=shared_font)
label2.pack(padx=5, pady=5)

root.mainloop()
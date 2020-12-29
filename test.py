import tkinter as tk
from tkinter.ttk import Treeview
import time

window = tk.Tk()
tree = Treeview(window, columns=("A", "B"))
tree.heading("A", command=lambda: print(tree.selection()))
tree.pack()

for i in range(5):
    tree.insert("", "end", values=(i, i**2))

window.mainloop()
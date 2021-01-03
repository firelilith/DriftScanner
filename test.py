"""import tkinter as tk
from tkinter.ttk import Treeview
import time

window = tk.Tk()
tree = Treeview(window, columns=("A", "B"))
tree.heading("A", command=lambda: print(tree.selection()))
tree.pack()

for i in range(5):
    tree.insert("", "end", values=(i, i**2))

window.mainloop()"""


def _shift(arr, n):
    if n >= 0:
        return np.concatenate((np.full(n, 0), arr[:-n]))
    else:
        return np.concatenate((arr[-n:], np.full(-n, 0)))


import numpy as np

array = np.array(np.random.random_integers(0, 200, 64)).reshape((8, 8))

middle = len(array) // 2

array = array.T

for column in range(len(array)):
    maximum, = np.where(array[column] == np.max(array[column]))
    maximum = maximum[0]
    print(maximum)
    print(_shift(array[column], middle - maximum))
    if maximum != 0:
        array[column] = _shift(array[column], middle - maximum)

print(array.T)


import tkinter as tk
from tkinter import simpledialog


class Prompt(simpledialog.Dialog):
    def __init__(self, parent):
        super(Prompt, self).__init__(parent)
    
    def body(self):
        pass


t = tk.Tk()



t.mainloop


"""class Prompt(tk.Toplevel):
    def __init__(self, parent):
        super(Prompt, self).__init__()
        self.master = parent

    def popup(self, out, params, title=""):
        self.out = out

        self.wm_title = title

        self.labels = []
        self.edits = []

        for i in params:
            self.labels.append(tk.Label(self, text=i))
            self.edits.append(tk.Entry(self))
        
        self.button = tk.Button(self, text="Ok", command=self.on_button)

        for l, e, n in zip(self.labels, self.edits, range(len(self.labels))):
            l.grid(row=n, column=0)
            e.grid(row=n, column=1)

        self.button.grid(column=1, sticky="ne")

        self.resizable(False,False)

        while True:
            self.after(100)

    def on_button(self):
        e = []
        for e in self.edits:
            if not e.get():
                quit()
            e.append(e.get())
        self.out = e
        self.destroy()


t = tk.Tk()

p = Prompt(t)

r = []

p.popup(r, ("1", "2", "3"))

print(r)

t.mainloop()"""
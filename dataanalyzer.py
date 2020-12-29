import tkinter as tk
import time
from tkinter import ttk
import numpy as np
import matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import matplotlib.pyplot as pyplot
from datasample import DataSample
matplotlib.use("TkAgg")


class DataAnalyzer:
    def __init__(self, parent):
        self.parent = parent
        self.window = tk.Toplevel()
        self.window.withdraw()

        self.window.title("Measurements")
        self.window.geometry("800x600")

        self.data = dict()
        self.sample_count = 0

        # Open data windows

        self.open_windows = []

        # File Menubar

        self.menubar = tk.Menu(self.window)

        self.menubar_file = tk.Menu(self.menubar, tearoff=0)
        self.menubar_file.add_command(label="Open", command=self.open_file)
        self.menubar_file.add_command(label="Save", command=self.save_file)
        self.menubar_file.add_separator()
        self.menubar_file.add_command(label="Close", command=self.close_window)

        self.menubar.add_cascade(label="File", menu=self.menubar_file)

        self.window.config(menu=self.menubar)

        # Layout
        columns = ("Title", "Brightness", "SNR", "StdDev from SNR", "StdDev", "StdDev/StdDev from SNR")

        self.datasheet = ttk.Treeview(self.window, columns=columns, selectmode='browse', show="headings")

        for col in columns:
            self.datasheet.heading(col, text=col, command=lambda _col=col: self.sort_by_column(_col, False))

        for h in columns:
            self.datasheet.heading(h, text=h)

        self.datasheet.pack(fill="both", expand=True, side="top")

        self.scrollbar = ttk.Scrollbar(self.datasheet)
        self.scrollbar.config(command=self.datasheet.yview)

        self.datasheet.config(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side="right", fill="y")

        # Buttons to get detailed info: (function_name, "Button Title")
        self.functions = ((self.f_show_crossection, "Show Crosssection"),
                          (self.f_show_flattened_line, "t-S-Graph"),
                          (self.f_show_SNR_StdDev_graph, "Compare SNR to StdDev"))

        for func in self.functions:
            b = tk.Button(master=self.window, command=func[0], text=func[1])
            b.pack(side="left")


        # Event handling

        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)


    def open_file(self):
        pass

    def save_file(self):
        pass

    def close_window(self):
        self.window.withdraw()

    def add_sample(self, sample):
        self.sample_count += 1
        key = self.datasheet.insert("", "end", values=(f"Measurement {self.sample_count}", *self.get_sample_values(sample)))
        self.data[key] = sample

    def get_sample_values(self, sample):
        return sample.signal, sample.snr, sample.get_stddev_from_SNR(), sample.get_stddev_from_numbers(), sample.get_stddev_from_numbers() / sample.get_stddev_from_SNR()

    def f_show_crossection(self):
        data = self.data[self.datasheet.focus()]
        title = self.datasheet.item(self.datasheet.focus())["text"]
        self.open_windows.append(GraphWindow(self.window, data, "Show Crosssection", title))

    def f_show_flattened_line(self):
        data = self.data[self.datasheet.focus()]
        title = self.datasheet.item(self.datasheet.focus())["text"]
        self.open_windows.append(GraphWindow(self.window, data, "t-S-Graph", title))

    def f_show_SNR_StdDev_graph(self):
        data = self.data[self.datasheet.focus()]
        title = self.datasheet.item(self.datasheet.focus())["text"]
        self.open_windows.append(GraphWindow(self.window, data, "Compare SNR to StdDev", title))

    # Event Handling

    def sort_by_column(self, col, reverse):
        l = [(self.datasheet.set(k, col), k) for k in self.datasheet.get_children("")]
        l.sort(reverse=reverse)

        for index, (val, k) in enumerate(l):
            self.datasheet.move(k, "", index)

        self.datasheet.heading(col, text=col, command=lambda _col=col: self.sort_by_column(_col, not reverse))

    def on_closing(self):
        self.window.withdraw()


class GraphWindow:
    def __init__(self, parent, sample, graph_type, title):
        self.sample = sample
        self.graph_type = graph_type

        self.parent = parent
        self.window = tk.Toplevel()
        self.window.withdraw()

        self.window.title(graph_type + ": " + title)
        self.window.geometry = "800x600"

        self.canvas = None

        self.f = Figure(dpi=200)

        if graph_type == "t-S-Graph" or graph_type == "Compare SNR to StdDev":
            self.slider = tk.Scale(self.window, from_=1, to=len(sample.data[0]) // 2, orient=tk.HORIZONTAL, label="Interval for moving average: ")
            self.slider.bind("<ButtonRelease-1>", self._slider_release_event)
            self.slider.pack(fill=tk.BOTH, expand=True)

        self.draw_figure(self.f, sample, graph_type)

        self.window.deiconify()


    def draw_figure(self, f, sample, graph_type, interval=1):
        if graph_type == "t-S-Graph":
            data = sample.get_flattened_moving_average(interval)
            axis_x = [i for i in range(interval, interval + len(data))]

            f.clear()

            a = f.add_subplot(111)
            a.set_ylabel("ADUs")
            a.set_xlabel("Pixel from Start")
            a.plot(axis_x, data)

        elif graph_type == "Show Crosssection":
            data = sample.get_crosssection()
            a = f.add_subplot(111)
            a.set_ylabel("ADUs")
            a.set_xlabel("Pixel from Centre")
            a.plot(np.array([i for i in range(len(data))]) - list(sample.get_crosssection()).index(max(sample.get_crosssection())), data)

        elif graph_type == "Compare SNR to StdDev":
            data = sample.get_flattened_moving_average(interval)
            axis_x = [i for i in range(interval, interval + len(data))]

            avg = sample.get_signal_per_pix_avg()
            stddev_theoretical = sample.get_moving_stddev_from_SNR(interval)
            stddev_numerical = sample.get_moving_stddev_from_numbers(interval)

            f.clear()

            a = f.add_subplot(111)
            a.set_ylabel("ADUs")
            a.set_xlabel("Pixel from Start")
            a.fill_between(axis_x, avg - stddev_theoretical, avg + stddev_theoretical, alpha=0.5, label="mean +- mean/SNR")
            a.fill_between(axis_x, avg - stddev_numerical, avg + stddev_numerical, alpha=0.25, label="mean +- StdDev")
            a.plot(axis_x, data)
            a.legend()

        else:
            raise ValueError

        if self.canvas:
            self.canvas.get_tk_widget().destroy()
            self.canvas.get_tk_widget().destroy()
        self.canvas = FigureCanvasTkAgg(self.f, self.window)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _redraw(self, val):
        self.draw_figure(self.f, self.sample, self.graph_type, interval=int(val))

    def _slider_release_event(self, event):
        self._redraw(self.slider.get())

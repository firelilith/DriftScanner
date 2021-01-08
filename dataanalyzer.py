import tkinter as tk
from tkinter import ttk, simpledialog, filedialog
import numpy as np

import json

import matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from scipy.stats import norm
from datasample import DataSample
matplotlib.use("TkAgg")


class DataAnalyzer:
    def __init__(self, parent):
        self.parent_app = parent
        self.parent = parent.root
        self.window = tk.Toplevel()

        self.window.title("Measurements")
        self.window.geometry("1200x600")

        self.data = dict()
        self.sample_count = 0

        # Open data windows

        self.open_windows = []

        # File Menubar
        """

        self.menubar = tk.Menu(self.window)

        self.menubar_file = tk.Menu(self.menubar, tearoff=0)
        self.menubar_file.add_command(label="Open", command=self.open_file)
        self.menubar_file.add_command(label="Save", command=self.save_file)
        self.menubar_file.add_separator()
        self.menubar_file.add_command(label="Close", command=self.close_window)

        self.menubar.add_cascade(label="File", menu=self.menubar_file)

        self.window.config(menu=self.menubar)
        """

        # Layout

        # Buttons to get detailed info: (function_name, "Button Title")
        self.file_functions = ((self.f_rename_sample, "Rename Sample"),
                               (self.f_delete_selected, "Delete Selected"),
                               (self.f_delete_all, "Delete All"),
                               (self.f_open, "Open Measurements"),
                               (self.f_save_selected, "Save Measurements"),
                               (self.f_save_headers, "Save only Headers"))

        self.display_functions = (((self.f_show_raw_crosssection, "Raw Crosssection"), (self.f_slope_adjusted_crosssection, "Slope adjusted Crossection"),
                                   (self.f_aligned_crosssection, "Aligned Crosssection")),

                                  ((self.f_show_maximum_wobble, "t-Y-Graph"), (self.f_slope_adjusted_t_y, "Slope adjusted t-Y-Graph")),
                                  ((self.f_show_flattened_line, "t-S-Graph"), (self.f_show_line_fit, "Get average line")),
                                  ((self.f_t_s_fourier, "t-S-Fourier"), (self.f_t_y_fourier, "t-Y-Fourier")),
                                  ((self.f_vertical_align, "Vertical align"), (self.f_binary_star_separation, "Binary Star Separation")))

        self.top_frame = tk.Frame(master=self.window)
        self.top_frame.pack(expand=False, fill=tk.X)
        for func in self.file_functions:
            b = tk.Button(master=self.top_frame, command=func[0], text=func[1])
            b.pack(side=tk.LEFT)

        self.columns = ("Title", "Altitude", "Brightness", "SNR", "Normalized StdDev", "Y-Variations over 5s")

        self.datasheet = ttk.Treeview(self.window, columns=self.columns, show="headings")

        for col in self.columns:
            self.datasheet.heading(col, text=col, command=lambda _col=col: self.sort_by_column(_col, False))

        for h in self.columns:
            self.datasheet.heading(h, text=h)

        self.datasheet.pack(fill="both", expand=True, side=tk.TOP)

        self.scrollbar = ttk.Scrollbar(self.datasheet)
        self.scrollbar.config(command=self.datasheet.yview)

        self.datasheet.config(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side="right", fill="y")

        self.bottom_frame = tk.Frame(master=self.window)
        self.bottom_frame.pack(expand=False, fill=tk.X)

        for j, group in enumerate(self.display_functions):
            for i, func in enumerate(group):
                b = tk.Button(master=self.bottom_frame, command=func[0], text=func[1])
                b.grid(column=j, row=i, sticky="NESW", padx=5)

        # Event handling

        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)


    def close_window(self):
        self.window.withdraw()

    def add_sample(self, sample, title=""):
        if not title:
            self.sample_count += 1
            title = f"Measurement {self.sample_count}"
        sample.title = title
        key = self.datasheet.insert("", "end", values=(title, *self.get_sample_values(sample)))
        self.data[key] = sample

    def get_sample_values(self, sample):
        return (sample.meta_info["altitude"],
                sample.signal,
                sample.snr,
                np.std(sample.get_flattened_line() / np.mean(sample.get_flattened_line())),
                np.std(sample.get_slope_adjusted_t_y(interval=round(5/sample.time_per_pix))))

    # -------------------------------------------------------------------------------------------------------------------------
    # Button functions for analysis

    def f_show_raw_crosssection(self):
        samples = self._get_selected()
        title = [self.datasheet.item(iid)["values"][0] for iid in self.datasheet.selection()]
        self.open_windows.append(GraphWindow(self, samples, "Raw Crosssection", title))

    def f_show_maximum_wobble(self):
        samples = self._get_selected()
        title = [self.datasheet.item(iid)["values"][0] for iid in self.datasheet.selection()]
        self.open_windows.append(GraphWindow(self, samples, "t-Y-Graph", title))

    def f_show_flattened_line(self):
        samples = self._get_selected()
        title = [self.datasheet.item(iid)["values"][0] for iid in self.datasheet.selection()]
        self.open_windows.append(GraphWindow(self, samples, "t-S-Graph", title))

    def f_show_line_fit(self):
        samples = self._get_selected()
        title = [self.datasheet.item(iid)["values"][0] for iid in self.datasheet.selection()]
        self.open_windows.append(GraphWindow(self, samples, "Average Line", title))

    def f_vertical_align(self):
        s = self.datasheet.focus()
        if s:
            sample = [self.data[s]]
            title = [self.datasheet.item(s)["values"][0]]
            self.open_windows.append(GraphWindow(self, sample, "Vertical align", title=title))

    def f_aligned_crosssection(self):
        samples = self._get_selected()
        title = [self.datasheet.item(iid)["values"][0] for iid in self.datasheet.selection()]
        self.open_windows.append(GraphWindow(self, samples, "Aligned Crosssection", title))

    def f_t_s_fourier(self):
        samples = self._get_selected()
        title = [self.datasheet.item(iid)["values"][0] for iid in self.datasheet.selection()]
        self.open_windows.append(GraphWindow(self, samples, "t-S-Fourier", title))

    def f_t_y_fourier(self):
        samples = self._get_selected()
        title = [self.datasheet.item(iid)["values"][0] for iid in self.datasheet.selection()]
        self.open_windows.append(GraphWindow(self, samples, "t-Y-Fourier", title))

    def f_slope_adjusted_t_y(self):
        samples = self._get_selected()
        title = [self.datasheet.item(iid)["values"][0] for iid in self.datasheet.selection()]
        self.open_windows.append(GraphWindow(self, samples, "Slope adjusted t-Y-Graph", title))

    def f_slope_adjusted_crosssection(self):
        samples = self._get_selected()
        title = [self.datasheet.item(iid)["values"][0] for iid in self.datasheet.selection()]
        self.open_windows.append(GraphWindow(self, samples, "Slope adjusted Crosssection", title))

    def f_binary_star_separation(self):
        s = self.datasheet.focus()
        if s:
            sample = [self.data[s]]
            title = [self.datasheet.item(s)["values"][0]]
            self.open_windows.append(GraphWindow(self, sample, "Binary Star Separation", title=title))

    # -------------------------------------------------------------------------------------------------------------------------
    # Button functions for analysis

    def f_rename_sample(self):
        s = self.datasheet.focus()
        if s:
            new_name = ""
            while not new_name or new_name in [self.datasheet.item(iid)["values"][0] for iid in self.datasheet.get_children()]:
                new_name = tk.simpledialog.askstring(f"Rename {self.datasheet.item(s)['values'][0]}", "Enter new title (must be unique)")
            v = self.datasheet.item(s)["values"]
            v[0] = new_name
            self.data[s].title = new_name
            self.datasheet.item(s, values=v)

    def f_delete_selected(self):
        samples = [iid for iid in self.datasheet.selection()]
        self.datasheet.delete(*samples)

    def f_delete_all(self):
        self.datasheet.delete(*self.datasheet.get_children())
        self.parent_app.graphics_clear_all()

        [self.parent_app.graphics_clear_label(key) for key in self.parent_app.image_label if not key.startswith("Custom")]

    def f_open(self):
        initial_dir = "/"
        if "directory" in self.parent_app.args:
            initial_dir = self.parent_app.args["directory"]
        file = tk.filedialog.askopenfilename(defaultextension=".json", initialdir=initial_dir)

        with open(file, "r") as f:
            samples = json.load(f)

        for s in samples:
            title = s
            if s.startswith("Measurement"):
                title = ""
            if s in [self.datasheet.item(child)["values"][0] for child in self.datasheet.get_children()]:
                title = title + "_1"

            self.add_sample(DataSample.build_from_json(samples[s]))

    def f_save_selected(self):
        initial_dir = "/"
        if "directory" in self.parent_app.args:
            initial_dir = self.parent_app.args["directory"]
        file = tk.filedialog.asksaveasfilename(defaultextension=".json", initialdir=initial_dir).strip()

        if not file.endswith(".json"):
            file += ".json"

        samples = {}

        for child in self.datasheet.get_children():
            samples[self.datasheet.item(child)["values"][0]] = self.data[child].get_json()

        with open(file, "w") as f:
            json.dump(samples, f)

    def f_save_headers(self):
        initial_dir = "/"
        if "directory" in self.parent_app.args:
            initial_dir = self.parent_app.args["directory"]
        file = tk.filedialog.asksaveasfilename(defaultextension=".json", initialdir=initial_dir).strip()

        if not file.endswith(".json"):
            file += ".json"

        samples = {}

        for child in self.datasheet.get_children():
            samples[self.datasheet.item(child)["values"][0]] = self.datasheet.item(child)["values"]

        with open(file, "w") as f:
            json.dump(samples, f)

    # Event Handling

    def sort_by_column(self, col, reverse):
        try:
            l = [(float(self.datasheet.set(k, col)), k) for k in self.datasheet.get_children("")]
        except ValueError:
            l = [(self.datasheet.set(k, col), k) for k in self.datasheet.get_children("")]

        l.sort(reverse=reverse)

        for index, (val, k) in enumerate(l):
            self.datasheet.move(k, "", index)

        self.datasheet.heading(col, text=col, command=lambda _col=col: self.sort_by_column(_col, not reverse))

    def on_closing(self):
        self.window.withdraw()

    def _get_selected(self):
        return [self.data[iid] for iid in self.datasheet.selection()]

class GraphWindow:
    def __init__(self, parent, samples, graph_type, title):
        self.samples = samples
        self.title = title
        self.graph_type = graph_type

        self.parent = parent
        self.window = tk.Toplevel()

        self.window.title(graph_type + ": " + ", ".join(title))
        self.window.geometry = "800x600"

        self.normalize = tk.BooleanVar()
        self.interval = tk.IntVar()
        self.custom_fwhm = tk.DoubleVar()

        self.frame = tk.Frame(self.window)
        self.frame.pack(expand=False, side=tk.TOP, fill=tk.X)

        self.canvas = None

        self.f = Figure()
        self.f.set_tight_layout(True)

        if graph_type in ("t-Y-Graph", "t-S-Graph",  "Average Line", "t-S-Fourier", "t-Y-Fourier", "Slope adjusted t-Y-Graph"):
            self.slider = tk.Scale(self.frame, from_=1, to=max(len(sample.data[0]) for sample in samples) // 2, orient=tk.HORIZONTAL, variable=self.interval, label="Interval for moving average: ")
            self.slider.bind("<ButtonRelease-1>", lambda x: self._redraw())
            self.slider.pack(fill=tk.BOTH, expand=True)

            self.slider.set(self.samples[0].delta_pix())

        if graph_type == "Binary Star Separation":
            self.slider = tk.Scale(self.frame, from_=0, to=samples[0].get_realigned_fwhm()[0] * 2, resolution=0.01 , orient=tk.HORIZONTAL, variable=self.custom_fwhm, label="FWHM")
            self.slider.set(samples[0].get_realigned_fwhm()[0])
            self.slider.bind("<ButtonRelease-1>", lambda x: self._redraw())
            self.slider.pack(fill=tk.BOTH, expand=True)

        if graph_type in ("t-S-Graph", "Raw Crosssection", "Aligned Crosssection", "Slope adjusted Crosssection"):
            self.normalize_check = tk.Checkbutton(self.frame, variable=self.normalize, offvalue=False, onvalue=True, text="Normalize", command=self._redraw)

            self.normalize_check.pack(side=tk.LEFT)

        self.draw_figure(self.f, samples, graph_type, interval=self.samples[0].delta_pix())

        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)

    def draw_figure(self, f, samples, graph_type, interval=1, normalize=False):

        if graph_type == "Raw Crosssection":
            data = [sample.get_crosssection() for sample in samples]

            f.clear()

            a = f.add_subplot(111, frameon=False)

            if not self.normalize.get():
                a.set_ylabel("ADUs")
            else:
                a.set_ylabel("Relative ADUs")
            a.set_xlabel("Pixel from Centre")

            for d, t in zip(data, self.title):
                if normalize:
                    graph_max = np.max(d)
                    d = d / graph_max
                offset = list(d).index(max(d))
                a.plot(np.array([i for i in range(len(d))]) - offset, d, label=t)

            if len(data) == 1:
                fwhm, height, lo, hi = samples[0].get_fwhm()
                if normalize: height /= graph_max
                a.hlines(height, lo, hi, label=f"FWHM = {fwhm}", color="C2", linestyles="dotted")

            a.legend(bbox_to_anchor=(1, 1), loc="upper left")

        elif graph_type == "t-Y-Graph":
            data = [sample.get_maximum_shift_moving_average(interval=interval) for sample in samples]
            axis_x = [i for i in range(interval, interval + max(map(len, data)))]

            f.clear()

            a = f.add_subplot(111, frameon=False)
            a.set_ylabel("Pixel from Mean")
            a.set_xlabel("Pixel from Start")

            for d, t in zip(data, self.title):
                a.plot(axis_x, d, label=t)

        elif graph_type == "t-S-Graph":
            data = [sample.get_flattened_moving_average(interval) for sample in samples]
            axis_x = [i for i in range(interval, interval + max(map(len, data)))]

            f.clear()

            a = f.add_subplot(111, frameon=False)
            if not self.normalize.get():
                a.set_ylabel("ADUs")
            else:
                a.set_ylabel("Relative ADUs")
            a.set_xlabel("Pixel from Start")

            for d, t in zip(data, self.title):
                if normalize: d = d / np.mean(d)
                a.plot(axis_x, d, label=t)

            a.legend(bbox_to_anchor=(1,1), loc="upper left")

        elif graph_type == "Average Line":
            data = np.array([sample.get_flattened_moving_average(interval) for sample in samples])
            axis_x = [i for i in range(interval, interval + max(map(len, data)))]

            for d in range(len(data)):
                data[d] = data[d] / np.mean(data[d])

            line = np.median(data, axis=0)

            f.clear()

            a = f.add_subplot(111, frameon=False)

            a.set_ylabel("Relative ADUs")
            a.set_xlabel("Pixel from Start")

            a.plot(axis_x, line, label="median")

        elif graph_type == "Vertical align":
            data = samples[0].data
            slope_adjusted_data = samples[0].get_slope_adjusted_data()
            aligned_data = samples[0].get_realigned_to_maximum()

            f.clear()

            ax1 = f.add_subplot(311, ylabel="raw")
            ax2 = f.add_subplot(312, ylabel="slope adjusted")
            ax3 = f.add_subplot(313, ylabel="realigned to maximum")

            ax1.imshow(data)
            ax2.imshow(slope_adjusted_data)
            ax3.imshow(aligned_data)

        elif graph_type == "Aligned Crosssection":
            data = [sample.get_realigned_crosssection() for sample in samples]

            f.clear()

            a = f.add_subplot(111, frameon=False)

            if not self.normalize.get():
                a.set_ylabel("ADUs")
            else:
                a.set_ylabel("Relative ADUs")
            a.set_xlabel("Pixel from Centre")

            for d, t in zip(data, self.title):
                if normalize:
                    graph_max = np.max(d)
                    d = d / graph_max
                offset = list(d).index(max(d))
                a.plot(np.array([i for i in range(len(d))]) - offset, d, label=t)

            if len(data) == 1:
                fwhm, height, lo, hi = samples[0].get_realigned_fwhm()
                if normalize: height /= graph_max
                a.hlines(height, lo, hi, label=f"FWHM = {fwhm}", color="C2", linestyles="dotted")

            a.legend(bbox_to_anchor=(1, 1), loc="upper left")

        elif graph_type == "t-S-Fourier":
            data = [sample.get_t_s_fourier(interval=interval) for sample in samples]
            data = [data[i][5:len(data[i]) // 2] for i in range(len(data))]
            axis_x = [i for i in range(5, len(data[0]) + 5)]

            f.clear()

            a = f.add_subplot(111, frameon=False)
            a.set_ylabel("Amplitude")
            a.set_xlabel("Frequency")

            a.set_xscale("log")
            a.set_yscale("log")

            for d, t in zip(data, self.title):
                a.plot(axis_x, d, label=t)

            a.legend(bbox_to_anchor=(1, 1), loc="upper left")

        elif graph_type == "t-Y-Fourier":
            data = [sample.get_t_y_fourier(interval=interval) for sample in samples]
            data = [data[i][5:len(data[i]) // 2] for i in range(len(data))]
            axis_x = [i for i in range(5, len(data[0]) + 5)]

            f.clear()

            a = f.add_subplot(111, frameon=False)
            a.set_ylabel("Amplitude")
            a.set_xlabel("Frequency")

            a.set_xscale("log")
            a.set_yscale("log")

            for d, t in zip(data, self.title):
                a.plot(axis_x, d, label=t)

            a.legend(bbox_to_anchor=(1, 1), loc="upper left")

        elif graph_type == "Slope adjusted t-Y-Graph":
            data = [sample.get_slope_adjusted_t_y(interval=interval) for sample in samples]
            axis_x = [i for i in range(interval, interval + max(map(len, data)))]

            f.clear()

            a = f.add_subplot(111, frameon=False)
            a.set_ylabel("Pixel from Max")
            a.set_xlabel("Pixel from Start")

            for d, t in zip(data, self.title):
                a.plot(axis_x, d, label=t)

            a.legend(bbox_to_anchor=(1, 1), loc="upper left")

        elif graph_type == "Slope adjusted Crosssection":
            data = [sample.get_slope_adjusted_crosssection() for sample in samples]

            f.clear()

            a = f.add_subplot(111, frameon=False)

            if not self.normalize.get():
                a.set_ylabel("ADUs")
            else:
                a.set_ylabel("Relative ADUs")
            a.set_xlabel("Pixel from Centre")

            for d, t in zip(data, self.title):
                if normalize:
                    graph_max = np.max(d)
                    d = d / graph_max
                offset = list(d).index(max(d))
                a.plot(np.array([i for i in range(len(d))]) - offset, d, label=t)

            if len(data) == 1:
                fwhm, height, lo, hi = samples[0].get_slope_adjusted_fwhm()
                if normalize: height /= graph_max
                a.hlines(height, lo, hi, label=f"FWHM = {fwhm}", color="C2", linestyles="dotted")

            a.legend(bbox_to_anchor=(1, 1), loc="upper left")

        elif graph_type == "Binary Star Separation":
            crosssection = samples[0].get_realigned_crosssection()
            fwhm = self.custom_fwhm.get()

            max_val = np.max(crosssection)

            x_val = np.arange(len(crosssection)) - list(crosssection).index(max_val)

            mu = 0
            sigma = fwhm / (2*np.sqrt(2*np.log(2)))

            if normalize:
                max_val = 1
                crosssection /= max_val

            f.clear()

            a = f.add_subplot(111, frameon=False)

            aprox = norm.pdf(x_val, mu, sigma)

            aprox = aprox * (1/np.max(aprox)) * max_val

            a.plot(x_val, crosssection, "C1", label="Raw Data")
            a.plot(x_val, aprox, "C2", label="Star 1")

            remainder = crosssection - aprox

            mu_remainder = list(remainder).index(np.max(remainder)) - list(crosssection).index(np.max(crosssection))

            aprox_remainder = norm.pdf(x_val, mu_remainder, sigma)

            aprox_remainder = aprox_remainder * (1/np.max(aprox_remainder)) * np.max(remainder)

            a.plot(x_val, aprox_remainder, "C4", label="Star 2")

            remainder_2 = remainder - aprox_remainder

            a.plot(x_val, remainder_2, "C3--", label=f"Error: {np.std(remainder_2)}")

            a.legend(bbox_to_anchor=(1, 1), loc="upper left")

        else:
            raise ValueError

        if self.canvas:
            self.canvas.get_tk_widget().destroy()
            self.canvas.get_tk_widget().destroy()
        self.canvas = FigureCanvasTkAgg(self.f, self.window)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _redraw(self):
        self.draw_figure(self.f, self.samples, self.graph_type, interval=self.interval.get(), normalize=self.normalize.get())

    def on_closing(self):
        self.parent.open_windows.remove(self)
        self.window.destroy()

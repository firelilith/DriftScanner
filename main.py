import tkinter as tk
from tkinter import filedialog, simpledialog, ttk

import re
import numpy as np
from astropy.io import fits
from PIL import Image, ImageTk

from dataanalyzer import DataAnalyzer
from datasample import DataSample


class App:
    def __init__(self, **kwargs):
        self.args = kwargs

        self.root = tk.Tk()
        self.root.title("DriftScanner")

        self.analyse_window = DataAnalyzer(self)

        self._init_vars()
        self._init_menu()
        self._init_display()

        # Event Handling

        self.root.bind("<Motion>", self.motion)
        self.root.bind("<Configure>", self.on_resize)
        self.root.bind("<Button-1>", self.on_left_click)
        self.root.bind("<Shift_L>", self._shift_down)
        self.root.bind("<KeyRelease-Shift_L>", self._shift_up)

        self.root.mainloop()

    def _debug(self):
        pass

    def _init_vars(self):
        self.working_file = None  # active .fits file
        self.working_data = None  # 2d numpy array of .fits data

        self.declination = 0
        self.time_per_pix = 0

        self.active_image = None  # active PhotoImage() object
        self.image_zoom = 1  # zoom level
        self.image_mode = "log"  # brightness curve mode

        # Graphics and display
        self.clicks = []  # stores most recent clicks, used in some measure modes
        self.graphics_temp = []  # graphics that get removed when a new mode is entered
        self.image_clearable = []  # graphic coordinates (x, y)
        self.graphics_clearable = []  # graphics ids that stay until manually removed
        self.image_label = []  # label coordinates + text (x, y, "text")
        self.graphics_label = []  # label ids

        self.operation = "idle"  # tool mode

        # Aperture settings, self-explanatory
        self.data_aperture_length = 100
        self.data_aperture_diameter = 15

        self.back_aperture_diameter_lower = 10
        self.back_aperture_offset_lower = 10
        self.back_aperture_diameter_upper = 10
        self.back_aperture_offset_upper = 10

        self.back_aperture_enabled_lower = True
        self.back_aperture_enabled_upper = True

        # Key statuses
        self.shift_pressed = False

        #
        self.data_samples = []
                             # store all used apertures as (datx, daty, data_aperture_length, data_aperture_diameter, back_aperture_enabled_lower, back_aperture_offset_lower,
        self.apertures = []  # back_aperture_diameter_lower, back_aperture_enabled_upper, back_aperture_offset_upper, back_aperture_diameter_upper)

    def _init_display(self):
        # widgets
        self.label_info = tk.Label(self.root)
        self.label_info.grid(row=0, column=0, sticky="nw")
        self.label_info_text = tk.StringVar()
        self.label_info.config(textvariable=self.label_info_text)

        self.label_tool = tk.Label(self.root)
        self.label_tool.grid(row=1, column=0, sticky="nw")
        self.label_tool_text = tk.StringVar()
        self.label_tool.config(textvariable=self.label_tool_text)

        self.frame = tk.Frame(self.root, width=800, height=800)

        self.canvas = tk.Canvas(self.frame, width=800, height=800)

        self.scrollbar_x = tk.Scrollbar(self.frame)
        self.scrollbar_x.grid(row=1, column=0, sticky="nw,ne")
        self.scrollbar_x.config(command=self.canvas.xview, orient="horizontal")

        self.scrollbar_y = tk.Scrollbar(self.frame)
        self.scrollbar_y.grid(row=0, column=1, sticky="nw,sw")
        self.scrollbar_y.config(command=self.canvas.yview, orient="vertical")

        self.frame.grid(row=2, column=0)
        self.canvas.grid(row=0, column=0)

        self.canvas.configure(yscrollcommand=self.scrollbar_y.set, xscrollcommand=self.scrollbar_x.set)

    def _init_menu(self):  # lots of boring stuff, configure the top menubar and submenus
        self.menubar = tk.Menu(self.root)  # main menubaar
        # -------
        self.filemenu = tk.Menu(self.menubar, tearoff=0)  # Menu to open a file or close the program

        self.filemenu_transform = tk.Menu(self.filemenu, tearoff=0)  # submenu for transformations
        self.filemenu_transform.add_command(label="Rotate Clockwise", command=self._transform_r_clockwise)
        self.filemenu_transform.add_command(label="Rotate Counterclockwise", command=self._transform_r_cclockwise)
        self.filemenu_transform.add_command(label="Mirror on Y", command=self._transform_m_y)
        self.filemenu_transform.add_command(label="Mirror on X", command=self._transform_m_x)

        self.filemenu.add_command(label="Open File", command=self.open_image)
        self.filemenu.add_cascade(label="Transform", menu=self.filemenu_transform)
        self.filemenu.add_command(label="Test Me", command=self._debug)  # debug command, TODO: remove when finalizing
        self.filemenu.add_separator()
        self.filemenu.add_command(label="Exit", command=self.root.quit)  # kills program
        # ------
        self.viewmenu = tk.Menu(self.menubar, tearoff=0)  # Menu to change view and brighness curve

        self.viewmenu_brightness = tk.Menu(self.viewmenu, tearoff=0)
        self.viewmenu_brightness.add_command(label="Linear", command=self._view_linear)
        self.viewmenu_brightness.add_command(label="Squareroot", command=self._view_sqrt)
        self.viewmenu_brightness.add_command(label="log", command=self._view_log)

        self.viewmenu_zoom = tk.Menu(self.viewmenu, tearoff=0)  # zoom image (slow and memory intensive, TODO: look for better way, maybe?)
        self.viewmenu_zoom.add_command(label="1x", command=self._zoom1)
        self.viewmenu_zoom.add_command(label="2x", command=self._zoom2)
        self.viewmenu_zoom.add_command(label="4x", command=self._zoom4)

        self.viewmenu_clear = tk.Menu(self.viewmenu, tearoff=0)
        self.viewmenu_clear.add_command(label="Clear last", command=self.graphics_clear_last)
        self.viewmenu_clear.add_command(label="Clear all", command=self.graphics_clear_all)

        self.viewmenu.add_cascade(label="Brightness", menu=self.viewmenu_brightness)
        self.viewmenu.add_cascade(label="Zoom", menu=self.viewmenu_zoom)
        self.viewmenu.add_cascade(label="Clear Graphics", menu=self.viewmenu_clear)
        self.viewmenu.add_command(label="Label", command=self.graphics_create_label)
        self.viewmenu.add_command(label="Clear labels", command=self.graphics_clear_labels)
        # -------
        self.measuremenu = tk.Menu(self.menubar, tearoff=0)  # Menu to measure basics

        self.measuremenu.add_command(label="Open Apertures", command=self.open_apertures)
        self.measuremenu.add_command(label="Save Apertures", command=self.save_apertures)

        self.measuremenu_aperture_size = tk.Menu(self.measuremenu, tearoff=0)  # set aperture length and diameter using popup prompts
        self.measuremenu_aperture_size.add_command(label="Set Scan Length", command=self.set_scan_length)
        self.measuremenu_aperture_size.add_command(label="Set Scan Diameter", command=self.set_scan_diameter)

        self.measuremenu.add_command(label="Measure Distance", command=self.measure_distance)  # distance between two points
        self.measuremenu.add_cascade(label="Aperture Settings", menu=self.measuremenu_aperture_size)
        self.measuremenu.add_command(label="Place Aperture", command=self.set_aperture)  # place apertures and measure data
        # -------
        self.menubar.add_cascade(label="File", menu=self.filemenu)
        self.menubar.add_cascade(label="View", menu=self.viewmenu)
        self.menubar.add_cascade(label="Measure", menu=self.measuremenu)

        self.root.config(menu=self.menubar)

    # ------------------------------------------------------------------------------------------------------------------------------
    # File operations

    def open_image(self, path=None, keep_labels=False):
        """open_image(path=None)\n
        Load .fits file using astropy.io\n
        Prompts user for file if no path specified"""

        if not path:  # ask user to open file, unless otherwise specified
            if "directory" in self.args:
                initial_dir = self.args["directory"]
            else:
                initial_dir = r"/"
            path = filedialog.askopenfilename(parent=self.root, initialdir=initial_dir, title="Select file")

        self.working_file = fits.open(path)
        self.working_data = self.working_file[0].data  # .fits files are a list of data sets, each having a header and data. the first is the one usually containing the image.
        self.image_zoom = 1  # TODO: if needed, set option to open different dataset

        if not keep_labels:
            self.graphics_clear_labels()

        self.graphics_clear_all()

        try:
            rdec = self.working_file[0].header["OBJCTDEC"]
            deg, min, sec = map(int, rdec.split(" "))
            self.declination = deg + min / 60 + sec / 3600
        except KeyError:
            self.root.withdraw()
            dec = ""
            while not (m := re.match(r"^(-?[0-9]{2})°(?:([0-5][0-9])'(?:([0-5][0-9](?:[\.,][0-9]+)?)(?:''|\"))?)?$", dec)):     # this regex matches every possible variation of declination in
                dec = simpledialog.askstring(title="", prompt="Declination of Image (XX°XX'XX,XX\")")                           # min/sec form and gives groups of °, ' and "
            self.root.deiconify()
            self.declination = float(m.group(1)) + (float(m.group(2)) / 60 if m.group(2) else 0) + (float(m.group(3).replace(",", ".")) / 3600 if m.group(3) else 0)
        finally:
            print("The declination is: ", self.declination)
            self.root.withdraw()
            arcsec_per_pix = float(simpledialog.askstring(title="", prompt="Arcsec per pixel"))
            self.root.deiconify()
            print(1 / (24 / 360.9856 / np.cos(np.deg2rad(self.declination))))
            self.time_per_pix = 24 / 360.9856 / np.cos(np.deg2rad(self.declination)) * arcsec_per_pix
            print(f"Time per pix is {self.time_per_pix}")

        self.display_image()

    def open_apertures(self, path=None):
        if not path:  # ask user to open file, unless otherwise specified
            if "directory" in self.args:
                initial_dir = self.args["directory"]
            else:
                initial_dir = r"/"
            path = filedialog.askopenfilename(parent=self.root, initialdir=initial_dir, title="Select aperture file")

        ap = np.genfromtxt(path, delimiter=",")

        for a in ap:
            x, y, l, w, lio, lof, lw, uio, uof, uw = list(map(int, a))
            self.data_aperture_length = l
            self.data_aperture_diameter = w
            self.back_aperture_enabled_lower = bool(lio)
            self.back_aperture_offset_lower = lof
            self.back_aperture_diameter_lower = lw
            self.back_aperture_enabled_upper = bool(uio)
            self.back_aperture_offset_upper = uof
            self.back_aperture_diameter_upper = uw

            self.click_set_aperture(x, y, x, y)

    def save_apertures(self, path=None):
        if not path:
            if "directory" in self.args:
                initial_dir = self.args["directory"]
            else:
                initial_dir = r"/"
            path = filedialog.asksaveasfilename(parent=self.root, initialdir=initial_dir, title="Save aperture file", defaultextension=".csv")

        np.savetxt(path, self.apertures, delimiter=",")





    # ------------------------------------------------------------------------------------------------------------------------------
    # Display
    def display_image(self, mode=None, zoom=None):
        """display_image(self, file, mode="linear")\n
        Diplays image to main canvas.\n
        Parameters:\n
        file: .fits object to be displayed\n
        mode: brightness display mode: linear, sqrt, log"""

        if not mode:
            if not self.image_mode:
                mode = "log"
            mode = self.image_mode

        if not zoom:
            if not self.image_zoom:
                zoom = 1
            zoom = self.image_zoom

        data = self.working_data

        if mode == "sqrt":  # reduce sharpness of brightness curve: squareroot or log10 on array to reduce span of values
            data = np.sqrt(np.abs(data))
        elif mode == "log":
            data = np.log10(np.abs(data))

        data = np.uint8(data / np.max(data) * 255)  # map values between (0, 255)

        self.img = ImageTk.PhotoImage(Image.fromarray(data, "L").resize((len(data), len(data[0]))))

        self.canvas.configure(scrollregion=(0, 0, *data.shape))  # set scrollable canvas size to data image size

        self.active_image = self.canvas.create_image(0, 0, image=self.img, anchor="nw")  # and print image to canvas

        self.graphics_clear_labels()  # kill all labels
        self.graphics_clear_all()  # kill all graphics

        for i in self.image_label:
            lx, ly, ltxt = i
            self.graphics_label.append(self.canvas.create_text(lx * self.image_zoom, ly * self.image_zoom, text=ltxt, fill="red", anchor="nw"))

        for i in self.image_clearable:
            x, y = i
            x, y = x * self.image_zoom, y * self.image_zoom
            self.graphics_clearable.append(self.canvas.create_rectangle(*self._get_ap_main(x, y), outline="blue"))

    def graphics_clear_last(self):
        if len(self.graphics_clearable):
            self.canvas.delete(self.graphics_clearable.pop(-1))

    def graphics_clear_all(self):
        [self.canvas.delete(g) for g in self.graphics_clearable]
        self.graphics_clearable = []
        [self.canvas.delete(g) for g in self.graphics_temp]
        self.graphics_temp = []

    def graphics_create_label(self):
        self.label_tool_text.set("Click to place a label. Shift-Click to place multiple.")
        self.operation = "label"

    def graphics_clear_labels(self):
        [self.canvas.delete(g) for g in self.graphics_label]
        self.graphics_label = []

    # ------------------------------------------------------------------------------------------------------------------------------
    # Event Handler

    def motion(self, event):  # Event handler: tracks mouse position on canvas and prints to label_info
        c = event.widget
        if self.working_data is not None and type(c) == type(tk.Canvas()):  # check if movement is on canvas and data is loaded
            c = event.widget

            x, y = c.canvasx(event.x), c.canvasy(event.y)

            x, y = int(x / self.image_zoom), int(y / self.image_zoom)
            hix, hiy = self.working_data.shape
            if (0 <= x and x < hix and 0 <= y and y < hiy):
                self.label_info_text.set(f"X: {x}  Y: {y} B: {self.working_data[y, x]}")  # give infos in top label: X, Y, Brightness

            if self.operation == "set_aperture":  # follow cursor with a aperture sized rectangle
                x, y = c.canvasx(event.x), c.canvasy(event.y)

                [self.canvas.delete(g) for g in self.graphics_temp]
                self.graphics_temp = []
                self.graphics_temp.append(self.canvas.create_rectangle(*self._get_ap_main(x, y), outline="blue"))
                self.graphics_temp.append(self.canvas.create_rectangle(*self._get_ap_lower(x, y), outline="blue", dash=(5, 5)))
                self.graphics_temp.append(self.canvas.create_rectangle(*self._get_ap_upper(x, y), outline="blue", dash=(5, 5)))
                self.graphics_temp.append(
                    self.canvas.create_line(x + self.data_aperture_length // 2 * self.image_zoom, y, x + (self.data_aperture_length // 2 + 20) * self.image_zoom, y, arrow="last", dash=(5, 5),
                                            fill="blue"))

    def on_resize(self, event):  # Event handler: resize canvas to window size
        if event.widget == self.root:
            w, h = event.width - 21, event.height - 63  # weird thing, without -21 and -63 window spazms out of control
            self.canvas.configure(width=w, height=h)

    def on_left_click(self, event):  # Event handler: Everything click related
        c = event.widget
        if self.working_data is not None and type(c) == type(tk.Canvas()):
            c = event.widget

            x, y = int(c.canvasx(event.x)), int(c.canvasy(event.y))
            datx, daty = x // self.image_zoom, y // self.image_zoom

            self.clicks.append((x, y))  # log clicks

            # Different tool modes from here on

            if self.operation == "distance":
                if len(self.clicks) > 2:
                    self.clicks = []
                    [self.canvas.delete(i) for i in self.graphics_temp]
                    self.graphics_temp = []
                    self.label_tool_text.set("Click twice to measure distance")

                elif len(self.clicks) == 1:
                    self.graphics_temp.append(self.canvas.create_oval(x - 10, y - 10, x + 10, y + 10, width=1, outline="red"))

                elif len(self.clicks) == 2:
                    self.graphics_temp.append(self.canvas.create_oval(x - 10, y - 10, x + 10, y + 10, width=1, outline="red"))
                    c1, c2 = self.clicks[0], self.clicks[1]
                    self.graphics_temp.append(self.canvas.create_line(*c1, *c2, fill="red", dash=(5, 5)))  # dashed line

                    d = np.sqrt((c1[0] - c2[0]) ** 2 + (c1[1] - c2[1]) ** 2) / self.image_zoom  # pythagoras to calculate distance, divide by zoom level
                    self.label_tool_text.set(f"Distance: {d:.2f}")

            if self.operation == "label":
                self.click_label(x, y, datx, daty)

            if self.operation == "set_aperture":
                self.click_set_aperture(x, y, datx, daty)

        if self.operation == "idle":
            self.label_tool_text.set("")

    def click_label(self, x, y, datx, daty):
        if not self.shift_pressed:
            self.operation = "idle"
        self.image_label.append((datx, daty, simpledialog.askstring("", "Label: ")))
        lx, ly, ltxt = self.image_label[-1]
        self.graphics_label.append(self.canvas.create_text(lx * self.image_zoom, ly * self.image_zoom, text=ltxt, fill="red", anchor="nw"))

    def click_set_aperture(self, x, y, datx, daty):
        if not self.shift_pressed:
            self.operation = "idle"

        self.apertures.append((datx, daty, self.data_aperture_length, self.data_aperture_diameter, self.back_aperture_enabled_lower, self.back_aperture_offset_lower, self.back_aperture_diameter_lower,
                               self.back_aperture_enabled_upper, self.back_aperture_offset_upper, self.back_aperture_diameter_upper))

        self.image_clearable.append((datx, daty))
        if not self.graphics_temp:
            self.graphics_temp.append(self.canvas.create_rectangle(*self._get_ap_main(x, y), outline="blue"))
        self.graphics_clearable.append(self.graphics_temp.pop(0))
        [self.canvas.delete(g) for g in self.graphics_temp]
        self.graphics_temp = []

        x1, y1, x2, y2 = self._get_ap_main(datx, daty)
        data = self.working_data[y1:y2, x1:x2]

        x1, y1, x2, y2 = self._get_ap_lower(datx, daty)
        back1 = self.working_data[y1:y2, x1:x2]

        x1, y1, x2, y2 = self._get_ap_upper(datx, daty)
        back2 = self.working_data[y1:y2, x1:x2]

        self.analyse_window.add_sample(DataSample(data, self.time_per_pix, back1, back2))
        self.analyse_window.window.deiconify()

    # ------------------------------------------------------------------------------------------------------------------------------
    # Basic Measure

    def measure_distance(self):
        self.operation = "distance"
        self.clicks = []
        self.label_tool_text.set("Click twice to measure distance")

    def set_scan_length(self):
        self.data_aperture_length = simpledialog.askinteger("", "Length: ")

    def set_scan_diameter(self):
        self.data_aperture_diameter = simpledialog.askinteger("", "Diameter: ")

    def set_aperture(self):
        self.operation = "set_aperture"
        self.label_tool_text.set("Click to place aperture. Shift-Click to place multiple.")
        [self.canvas.delete(g) for g in self.graphics_temp]
        self.graphics_temp = []

    # ------------------------------------------------------------------------------------------------------------------------------
    # Util functions and workarounds

    def _view_linear(self):
        self.image_mode = "linear"
        self.display_image()

    def _view_sqrt(self):
        self.image_mode = "sqrt"
        self.display_image()

    def _view_log(self):
        self.image_mode = "log"
        self.display_image()

    def _zoom1(self):
        self.display_image(zoom=1)

    def _zoom2(self):
        self.display_image(zoom=2)

    def _zoom4(self):
        self.display_image(zoom=4)

    def _transform_m_x(self):
        self.working_data = np.flipud(self.working_data)
        self.display_image()

    def _transform_m_y(self):
        self.working_data = np.fliplr(self.working_data)
        self.display_image()

    def _transform_r_cclockwise(self):
        self.working_data = np.rot90(self.working_data)
        self.display_image()

    def _transform_r_clockwise(self):
        self.working_data = np.rot90(self.working_data, 3)
        self.display_image()

    def _shift_down(self, event):
        self.shift_pressed = True

    def _shift_up(self, event):
        self.shift_pressed = False

    def _get_ap_main(self, x, y):  # return coords for main aperture based on mouse coordinates
        x1 = x
        y1 = y - int(np.floor(self.data_aperture_diameter * self.image_zoom / 2))
        x2 = x + self.data_aperture_length * self.image_zoom
        y2 = y + int(np.ceil(self.data_aperture_diameter * self.image_zoom / 2))
        return (x1, y1, x2, y2)

    def _get_ap_lower(self, x, y):  # same for lower background aperture
        x1 = x
        y2 = y + int((np.ceil(self.data_aperture_diameter / 2)) + self.back_aperture_diameter_upper + self.back_aperture_offset_upper) * self.image_zoom
        x2 = x + self.data_aperture_length * self.image_zoom
        y1 = y + int((np.ceil(self.data_aperture_diameter / 2)) + self.back_aperture_offset_upper) * self.image_zoom
        return (x1, y1, x2, y2)

    def _get_ap_upper(self, x, y):  # upper background aperture
        x1 = x
        y2 = y - int((np.floor(self.data_aperture_diameter / 2)) + self.back_aperture_offset_lower) * self.image_zoom
        x2 = x + self.data_aperture_length * self.image_zoom
        y1 = y - int((np.floor(self.data_aperture_diameter / 2)) + self.back_aperture_diameter_lower + self.back_aperture_offset_lower) * self.image_zoom
        return (x1, y1, x2, y2)


if __name__ == "__main__":
    app = App(directory=r"C:\Users\ole\OneDrive\Desktop\Jufo\Daten")

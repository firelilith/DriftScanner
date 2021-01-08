import numpy as np
from matplotlib import pyplot
import json

from scipy.optimize import curve_fit

from datasample import DataSample

def plot_altitude_stddev(json_path):
    data = {}
    altitudes = {}



    with open(json_path, "r") as f:
        json_data = json.load(f)
        for measurement in json_data:
            s = DataSample.build_from_json(json_data[measurement])

            data[measurement] = []
            altitudes[measurement] = s.meta_info["altitude"]

            for interval_s in range(10):
                data[measurement].append(np.std(s.get_slope_adjusted_t_y(interval=round(interval_s / s.time_per_pix))))

    x_values = list(data.keys())
    y_values = np.array([data[i] for i in x_values]).T

    x_values = list(map(lambda x: float(altitudes[x].strip().strip("deg")), x_values))

    pyplot.plot(x_values, y_values)
    pyplot.show()

def plot_altitude_stddev_from_headers(json_path, num=0):
    x_val = []
    y_val = []
    color = ["b", "r"]

    with open(json_path, "r") as f:
        json_data = json.load(f)
        for measurement in json_data:
            altitude = float(json_data[measurement][1].strip("deg"))
            if not json_path==r"C:\Users\ole\OneDrive\Desktop\Jufo\Daten\20201218\brightest_stars_headers.json" or not (71 <= altitude <= 86) or (altitude==80 and measurement=="Measurement 27"):
                if altitude not in x_val:
                    x_val.append(altitude)
                    y_val.append([json_data[measurement][-1]])
                else:
                    y_val[x_val.index(altitude)].append(json_data[measurement][-1])


    y_val = [list(map(float, i)) for i in y_val]
    y_val = np.array(list(map(np.mean, y_val)))

    x_val = np.array(x_val)
    y_val = np.array(y_val)

    function_poly = lambda x, a, b, c: a*x**2 + b*x + c
    function_exp = lambda x, a, b: a * np.exp(-b * x)
    function_cos = lambda x, a, b: a / (np.cos(np.pi/2 - (x / 180 * np.pi)) + b)

    (a_poly, b_poly, c_poly), res_poly = curve_fit(function_poly, x_val, y_val)
    (a_exp, b_exp), res_exp = curve_fit(function_exp, x_val, y_val)
    (a_cos, b_cos), res_cos = curve_fit(function_cos, x_val, y_val)

    error_poly = np.std(y_val - function_poly(x_val, a_poly, b_poly, c_poly))
    error_exp = np.std(y_val - function_exp(x_val, a_exp, b_exp))
    error_cos = np.std(y_val - function_cos(x_val, a_cos, b_cos))

    plot_x = np.linspace(.5, 89.5, 900)

    #pyplot.plot(plot_x, function_poly(plot_x, a_poly, b_poly, c_poly), label=f"Polynomial: S={error_poly}")
    #pyplot.plot(plot_x, function_exp(plot_x, a_exp, b_exp), label=f"Exponential: S={+error_exp}")
    pyplot.plot(plot_x, function_cos(plot_x, a_cos, b_cos), color[num], label=f"1/cos: S={error_cos}")

    pyplot.plot(x_val, y_val, color[num]+"+")
    pyplot.xlim(90, 0)
    pyplot.ylim(0, max(y_val))

    pyplot.legend()
    pyplot.tight_layout()
    #pyplot.show()

    pyplot.savefig(json_path[:-5]+".png")


if __name__ == '__main__':
    plot_altitude_stddev_from_headers(r"C:\Users\ole\OneDrive\Desktop\Jufo\Daten\20201216\sky_scan_headers.json", num=0)
    plot_altitude_stddev_from_headers(r"C:\Users\ole\OneDrive\Desktop\Jufo\Daten\20201218\brightest_stars_headers.json", num=1)

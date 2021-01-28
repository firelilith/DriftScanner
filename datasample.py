import numpy as np


class DataSample:
    def __init__(self, data, time_per_pix, background1, background2, meta_info={},title="", readout_noise=12.7865):
        """DataSample(data, time_per_pix, background, background2, readout_noise)
        Param:
        data = 2d numpy array-like object: drift data
        time_per_pix = float: drift speed

        takes drift scan data for one drift and gives access to evaluation functions"""
        self.data_raw = data
        self.background1 = background1
        self.background2 = background2
        self.time_per_pix = time_per_pix
        self.readout_dev = readout_noise

        self.title = title

        self.data = self._data()

        self.signal_raw = self._signal_raw()
        self.signal = self._signal_background()

        self.snr = self.get_snr()

        self.meta_info = meta_info

        self.interval_time = 1

        # print(self.background1, self.background2, self._background_avg())
        # print(self.data_raw, self.data)
        # print(self.signal_raw, self.signal, self.snr)

    def get_json(self):
        data = dict()
        data["title"] = self.title
        data["raw_data"] = list(map(lambda x: list(map(float, x)), list(self.data_raw)))
        data["background1"] = list(map(lambda x: list(map(float, x)), list(self.background1)))
        data["background2"] = list(map(lambda x: list(map(float, x)), list(self.background2)))
        data["time_per_pix"] = self.time_per_pix
        data["readout_noise"] = self.readout_dev
        data["meta_info"] = self.meta_info

        return data

    @classmethod
    def build_from_json(cls, json):
        title = json["title"]
        data = np.array(json["raw_data"])
        background1 = np.array(json["background1"])
        background2 = np.array(json["background2"])
        time_per_pix = json["time_per_pix"]
        readout_noise = json["readout_noise"]
        meta_info = json["meta_info"]

        if "time_per_pix" not in meta_info:
            meta_info["time_per_pix"] = None

        return DataSample(data, time_per_pix, background1, background2, meta_info=meta_info, title=title, readout_noise=readout_noise)

    def _adjust_bounds(self, start, stop, interval=0):
        if start > stop:
            start, stop = stop, start
        if start < 0:
            start = 0
        if stop <= 0 or stop > len(self.data_raw[0]):
            stop = len(self.data_raw[0])

        if interval > (stop-start) / 2:
            interval = 1

        return start, stop, interval

    def _data(self, start=0, stop=0, avg_mode="median"):
        start, stop, _ = self._adjust_bounds(start, stop)

        bg_avg = self._background_avg(start=start, stop=stop, avg_mode=avg_mode)
        return self.data_raw - bg_avg

    def _background_avg(self, start=0, stop=0, avg_mode="median"):
        background_avg = 0
        start, stop, _ = self._adjust_bounds(start, stop)

        bg1 = self.background1[:, start:stop]
        bg2 = self.background1[:, start:stop]

        if avg_mode == "mean":
            background_avg = np.mean(np.array((bg1, bg2)))
        if avg_mode == "median":
            background_avg = np.median(np.array((bg1, bg2)))

        return background_avg

    def _signal_raw(self, start=0, stop=0):
        start, stop, _ = self._adjust_bounds(start, stop)

        subarr = self.data_raw[:, start:stop]
        return np.sum(subarr)

    def _signal_background(self, start=0, stop=0):
        start, stop, _ = self._adjust_bounds(start, stop)

        subarr = self.data[:, start:stop]
        return np.sum(subarr)

    def delta_pix(self, time=None):        # Calculates the appropriate pixel interval width for a given time interval based on the declination
        if not time:
            time = self.interval_time

        v_drift = 1 / self.meta_info["time_per_pix"] if self.meta_info["time_per_pix"] else 1
        return int(abs(v_drift * time))

    def get_snr(self, start=0, stop=0, readout_time=25, readout_dev=0):
        start, stop, _ = self._adjust_bounds(start, stop)

        signal = self._signal_background(start=start, stop=stop)

        if self.background1.shape == self.background2.shape:
            bg = np.array((self.background1[:, start:stop], self.background2[:, start:stop]))
        else:
            if sum(self.background1.shape) > sum(self.background2.shape):
                bg = self.background1
            else:
                bg = self.background2

        background_dev = np.std(bg)

        time = self.time_per_pix * (stop - start)

        pixel_count = np.size(self.data, 0) * (stop - start)

        snr = signal / np.sqrt(signal + time * pixel_count * (background_dev + self.readout_dev**2))

        return snr

    def get_crosssection(self, start=0, stop=0):  # returns view parallel to drift direction, useful for calculating FWHM
        start, stop, _ = self._adjust_bounds(start, stop)

        section = self.data[:, start:stop]
        crosssection = np.sum(section, axis=1)

        return crosssection

    def get_flattened_line(self, start=0, stop=0):  # returns view orthogonal to drift direction, useful for temporal evaluation
        start, stop, _ = self._adjust_bounds(start, stop)

        section = self.data[:, start:stop]
        flattened_line = np.sum(section, axis=0)

        return flattened_line

    def get_signal_per_pix_avg(self, start=0, stop=0):
        start, stop, _ = self._adjust_bounds(start, stop)

        return sum(self.get_flattened_line(start=start, stop=stop)) / (stop - start)

    def get_stddev_from_SNR(self, start=0, stop=0):
        start, stop, _ = self._adjust_bounds(start, stop)

        return self.get_signal_per_pix_avg(start, stop) / self.get_snr(start, stop)

    def get_stddev_from_numbers(self, start=0, stop=0):
        start, stop, _ = self._adjust_bounds(start, stop)

        return np.std(self.get_flattened_line(start, stop))

    def get_flattened_moving_average(self, interval=None, start=0, stop=0):
        if not interval:
            interval = self.delta_pix(time=self.interval_time)

        start, stop, interval = self._adjust_bounds(start, stop, interval)

        line = self.get_flattened_line(start, stop)

        mvg_avg = []
        for i in range(len(line) - interval):
            mvg_avg.append(np.average(line[i:i+interval]))

        return np.array(mvg_avg)

    def get_moving_stddev_from_SNR(self, interval=None, start=0, stop=0):
        if not interval:
            interval = self.delta_pix(time=self.interval_time)

        start, stop, interval = self._adjust_bounds(start, stop, interval)

        stddev = []
        for i in range(stop - start - interval):
            stddev.append(self.get_stddev_from_SNR(i, i + interval))

        return np.array(stddev)

    def get_moving_stddev_from_numbers(self, interval=None, start=0, stop=0):
        if not interval:
            interval = self.delta_pix(time=self.interval_time)

        start, stop, interval = self._adjust_bounds(start, stop, interval)

        data = self.get_flattened_line(start, stop)

        stddev = []
        for i in range(stop - start - interval):
            stddev.append(self.get_stddev_from_numbers(i, i + interval))

        return np.array(stddev)

    def get_realigned_to_maximum(self, vertical_interval=5, start=0, stop=0):
        def _shift(col, n):
            if n >= 0:
                return np.concatenate((np.full(n, 0), col[:-n]))
            else:
                return np.concatenate((col[-n:], np.full(-n, 0)))

        start, stop, _ = self._adjust_bounds(start, stop)

        data = self.data[:, start:stop].T.copy()
        middle = len(self.data) // 2

        prev = None

        for column in range(len(data)):
            max = 0
            maxi = 0

            if not prev:
                shifts = range(len(data[column]) - vertical_interval)
            else:
                shifts = range(prev - 1 - vertical_interval, prev + 1)

            for i in shifts:
                if np.sum(data[column, i:i+vertical_interval]) > max:
                    max = np.sum(data[column, i:i+vertical_interval])
                    maxi = i + vertical_interval // 2

            prev = maxi

            if middle-maxi != 0:
                data[column] = _shift(data[column], middle - maxi)

        return data.T

    def get_realigned_crosssection(self, vertical_interval=5, start=0, stop=0):
        start, stop, _ = self._adjust_bounds(start, stop)

        return np.sum(self.get_realigned_to_maximum(vertical_interval=vertical_interval, start=start, stop=stop), axis=1)

    def get_fwhm(self, start=0, stop=0):
        def get_interpolated(y, lo, hi):
            return (y - lo) / (hi - lo)

        start, stop, _ = self._adjust_bounds(start, stop)

        data = self.get_crosssection(start=start, stop=stop)

        maximum = np.max(data)

        pos_max = list(data).index(maximum)

        lo, hi = pos_max, pos_max

        for i in range(pos_max, 1, -1):
            if data[i-1] < maximum / 2:
                lo = i
                break

        for i in range(pos_max, len(data)-1):
            if data[i+1] < maximum / 2:
                hi = i
                break

        lo += get_interpolated(maximum / 2, data[lo], data[lo+1]) - pos_max
        hi += get_interpolated(maximum / 2, data[hi], data[hi+1]) - pos_max

        return hi-lo, maximum / 2, lo, hi


    def get_realigned_fwhm(self, start=0, stop=0):
        def get_interpolated(y, lo, hi):
            return (y - lo) / (hi - lo)

        start, stop, _ = self._adjust_bounds(start, stop)

        data = self.get_realigned_crosssection(start=start, stop=stop)

        maximum = np.max(data)

        pos_max = list(data).index(maximum)

        lo, hi = pos_max, pos_max

        for i in range(pos_max, 0, -1):
            if data[i] < maximum / 2:
                lo = i
                break

        for i in range(pos_max, len(data) - 1):
            if data[i + 1] < maximum / 2:
                hi = i
                break

        lo += get_interpolated(maximum / 2, data[lo], data[lo+1]) - pos_max
        hi += get_interpolated(maximum / 2, data[hi], data[hi+1]) - pos_max

        return hi - lo, maximum / 2, lo, hi

    def get_maximum_shift(self, vertical_interval=5, start=0, stop=0):
        start, stop, _ = self._adjust_bounds(start, stop)

        max_positions = []

        middle = len(self.data) // 2

        for column in self.data[:, start:stop].T:
            max = 0
            maxi = 0
            for i in range(len(column) - vertical_interval):
                if np.sum(column[i:i + vertical_interval]) > max:
                    max = np.sum(column[i:i + vertical_interval])
                    maxi = i + vertical_interval // 2

            max_positions.append(middle - maxi)

        return max_positions

    def get_maximum_shift_moving_average(self, interval=None, vertical_interval=5, start=0, stop=0):
        if not interval:
            interval = self.delta_pix(time=self.interval_time)

        start, stop, interval = self._adjust_bounds(start, stop, interval)

        max_shift = self.get_maximum_shift(vertical_interval=vertical_interval, start=start, stop=stop)

        avg = [np.mean(max_shift[i:i+interval]) for i in range(start, stop-interval)]

        return np.array(avg)

    def get_t_s_fourier(self, interval=None, start=0, stop=0):
        start, stop, interval = self._adjust_bounds(start, stop, interval)

        data = self.get_flattened_moving_average(interval, start, stop)

        fourier = np.fft.fft(data)

        return np.abs(fourier)

    def get_t_y_fourier(self, interval=None, start=0, stop=0):
        if not interval:
            interval = self.delta_pix(time=self.interval_time)

        start, stop, interval = self._adjust_bounds(start, stop, interval)

        data = self.get_maximum_shift_moving_average(interval=interval, vertical_interval=5, start=start, stop=stop)

        fourier = np.fft.fft(data)

        return np.abs(fourier)

    def get_slope_adjusted_t_y(self, interval=None, start=0, stop=0):
        if not interval:
            interval = self.delta_pix(time=self.interval_time)

        start, stop, interval = self._adjust_bounds(start, stop, interval)

        data = self.get_maximum_shift_moving_average(interval=interval, start=start, stop=stop)

        data_x = np.arange(len(data)) - len(data) // 2

        regression_coef = np.polyfit(data_x, data, 1)

        fitted = np.poly1d(regression_coef)(data_x)

        return data - fitted

    def get_slope_adjusted_data(self, start=0, stop=0):
        def _shift(col, n):
            if n > 0:
                return np.concatenate((np.full(n, 0), col[:-n]))
            elif n < 0:
                return np.concatenate((col[-n:], np.full(-n, 0)))
            else:
                return col

        start, stop, _ = self._adjust_bounds(start, stop)

        data = self.data[start:stop].T.copy()

        shift_data = self.get_maximum_shift_moving_average(interval=1, start=start, stop=stop)

        data_x = np.arange(len(shift_data))

        regression_coef = np.polyfit(data_x - len(data) // 2, shift_data, 1)

        realignment_values = np.poly1d(regression_coef)(data_x)

        for i in range(len(realignment_values)):
            data[i] = _shift(data[i], int(realignment_values[i]))

        return data.T

    def get_slope_adjusted_crosssection(self, start=0, stop=0):
        start, stop, _ = self._adjust_bounds(start, stop)

        return np.sum(self.get_slope_adjusted_data(start=start, stop=stop), axis=1)

    def get_slope_adjusted_fwhm(self, start=0, stop=0):
        def get_interpolated(y, lo, hi):
            return (y - lo) / (hi - lo)

        start, stop, _ = self._adjust_bounds(start, stop)

        data = self.get_slope_adjusted_crosssection(start=start, stop=stop)

        maximum = np.max(data)

        pos_max = list(data).index(maximum)

        lo, hi = pos_max, pos_max

        for i in range(pos_max, 0, -1):
            if data[i] < maximum / 2:
                lo = i
                break

        for i in range(pos_max, len(data) - 1):
            if data[i + 1] < maximum / 2:
                hi = i
                break

        lo += get_interpolated(maximum / 2, data[lo], data[lo+1]) - pos_max
        hi += get_interpolated(maximum / 2, data[hi], data[hi+1]) - pos_max

        return hi - lo, maximum / 2, lo, hi


  def get_luminosity(start=0, stop=0):
    start, stop, _ = self._adjust_bounds(start, stop)

    luminosity = np.sum(self.data) / (len(self.data[0]) * self.time_per_pix)

    return luminosity, luminosity / self.snr

  def get_realigned_luminosity(fwhm_amount=3, start=0, stop=0):
    start, stop, _ = self._adjust_bounds(start, stop)
    
    data = get_realigned_crosssection(start, stop)

    fwhm = self.get_realigned_fwhm(start, stop)

    max_pos = list(data).index(np.max(data))

    cutout = max_pos - fwhm / 2 * fwhm_amount, max_pos + fwhm / 2 * fwhm_amount

    luminosity = np.sum(data[cutout]) / (len(self.data[0]) * self.time_per_pix)

    return luminosity, luminosity / self.get_realigned_snr(fwhm_amount, start, stop)

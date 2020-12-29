import numpy as np


class DataSample:
    def __init__(self, data, time_per_pix, background1, background2, readout_noise=0):
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

        self.fwhm = 0

        self.data = self._data()

        self.signal_raw = self._signal_raw()
        self.signal = self._signal_background()

        self.snr = self.get_snr()

        # print(self.background1, self.background2, self._background_avg())
        # print(self.data_raw, self.data)
        # print(self.signal_raw, self.signal, self.snr)

    def _adjust_bounds(self, start, stop):
        if start > stop:
            start, stop = stop, start
        if start < 0:
            start = 0
        if stop <= 0 or stop > len(self.data_raw[0]):
            stop = len(self.data_raw[0])

        return start, stop

    def _data(self, start=0, stop=0, avg_mode="median"):
        start, stop = self._adjust_bounds(start, stop)
        bg_avg = self._background_avg(start=start, stop=stop, avg_mode=avg_mode)
        return self.data_raw - bg_avg

    def _background_avg(self, start=0, stop=0, avg_mode="median"):
        background_avg = 0
        start, stop = self._adjust_bounds(start, stop)

        bg1 = self.background1[:, start:stop]
        bg2 = self.background1[:, start:stop]

        if avg_mode == "mean":
            background_avg = np.mean(np.array((bg1, bg2)))
        if avg_mode == "median":
            background_avg = np.median(np.array((bg1, bg2)))

        return background_avg

    def _signal_raw(self, start=0, stop=0):
        start, stop = self._adjust_bounds(start, stop)

        subarr = self.data_raw[:, start:stop]
        return np.sum(subarr)

    def _signal_background(self, start=0, stop=0):
        start, stop = self._adjust_bounds(start, stop)

        subarr = self.data[:, start:stop]
        return np.sum(subarr)

    def get_snr(self, start=0, stop=0):
        start, stop = self._adjust_bounds(start, stop)

        signal = self._signal_background(start=start, stop=stop)

        background_dev = np.std(np.array((self.background1[:, start:stop], self.background2[:, start:stop])))

        time = self.time_per_pix * (stop - start)

        pixel_count = np.size(self.data, 0) * (stop - start)

        snr = signal / np.sqrt(signal + time * pixel_count * (background_dev + self.readout_dev))

        return snr

    def get_crosssection(self, start=0, stop=0):  # returns view parallel to drift direction, useful for calculating FWHM
        start, stop = self._adjust_bounds(start, stop)

        section = self.data_raw[:, start:stop]
        crosssection = np.sum(section, axis=1)

        return crosssection

    def get_flattened_line(self, start=0, stop=0):  # returns view orthogonal to drift direction, useful for temporal evaluation
        start, stop = self._adjust_bounds(start, stop)

        section = self.data[:, start:stop]
        flattened_line = np.sum(section, axis=0)

        return flattened_line

    def get_signal_per_pix_avg(self, start=0, stop=0):
        start, stop = self._adjust_bounds(start, stop)

        return sum(self.get_flattened_line(start=start, stop=stop)) / (stop - start)

    def get_stddev_from_SNR(self, start=0, stop=0):
        start, stop = self._adjust_bounds(start, stop)

        return self.get_signal_per_pix_avg(start, stop) / self.get_snr(start, stop)

    def get_stddev_from_numbers(self, start=0, stop=0):
        start, stop = self._adjust_bounds(start, stop)

        return np.std(self.get_flattened_line(start, stop))

    def get_flattened_moving_average(self, interval, start=0, stop=0):
        start, stop = self._adjust_bounds(start, stop)

        line = self.get_flattened_line(start, stop)

        mvg_avg = []
        for i in range(len(line) - interval):
            mvg_avg.append(np.average(line[i:i+interval]))

        return np.array(mvg_avg)

    def get_moving_stddev_from_SNR(self, interval, start=0, stop=0):
        start, stop = self._adjust_bounds(start, stop)

        stddev = []
        for i in range(stop - start - interval):
            stddev.append(self.get_stddev_from_SNR(i, i + interval))

        return np.array(stddev)

    def get_moving_stddev_from_numbers(self, interval, start=0, stop=0):
        start, stop = self._adjust_bounds(start, stop)

        data = self.get_flattened_line(start, stop)

        stddev = []
        for i in range(stop - start - interval):
            stddev.append(self.get_stddev_from_numbers(i, i + interval))

        return np.array(stddev)

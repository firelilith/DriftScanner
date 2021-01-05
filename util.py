import numpy as np
from astropy.io import fits
from os import listdir
from skimage.feature import peak_local_max
import matplotlib.pyplot as plt


def detect_stars(data_image, threshold_abs=None, min_separation=20, scan_length=100, scan_diameter=15):
    """Takes and image and finds local maxima, returns points and checks if drift line needs to be flipped for analyzer to work.
    reduces or increases threshold, if it finds less than 10 or more than 100 local maxima"""
    if not threshold_abs:
        threshold_abs = np.max(data_image) / 20

    xy = peak_local_max(data_image, min_distance=min_separation, threshold_abs=threshold_abs)
    y, x = [i[0] for i in xy], [i[1] for i in xy]

    points = list(zip(y, x))

    if len(points) < 10:
        print(f"found {len(points)} local maxima, decreasing threshold to {.5*threshold_abs}.")
        points, should_flip, should_rotate_cw = detect_stars(data_image, threshold_abs=.5*threshold_abs, min_separation=min_separation, scan_length=scan_length, scan_diameter=scan_diameter)

    elif len(points) > 100:
        print(f"found {len(points)} local maxima, increasing threshold to {2*threshold_abs}.")
        points, should_flip, should_rotate_cw = detect_stars(data_image, threshold_abs=2*threshold_abs, min_separation=min_separation, scan_length=scan_length, scan_diameter=scan_diameter)

    else:
        should_flip = []
        should_rotate_cw = []

        for p in points:
            y, x = p
            w = scan_diameter // 2
            try:
                up = np.sum(data_image[y - scan_length:y - 5, x - w:x + w])
                down = np.sum(data_image[y + 5:y + scan_length, x - w:x + w])
                left = np.sum(data_image[y - w:y + w, x - scan_length:x - 5])
                right = np.sum(data_image[y - w:y + w, x + 5:x + scan_length])

                m = max(up, down, left, right)

                rotate_cw = m == up or m == down
                flip = m == left or m == down

                should_rotate_cw.append(rotate_cw)
                should_flip.append(flip)

            except IndexError as e:
                pass

        print(f"Flip: {should_flip.count(True)}/{len(should_flip)}, Rotate: {should_rotate_cw.count(True)}/{len(should_rotate_cw)}")

        if should_flip.count(True) > should_flip.count(False):
            should_flip = True
        else:
            should_flip = False

        if should_rotate_cw.count(True) > should_rotate_cw.count(False):
            should_rotate_cw = True
        else:
            should_rotate_cw = False

    return points, should_flip, should_rotate_cw

def get_dark_noise(directory_of_darks, quick=False):
    """returns the average standard deviation for the difference of two darks. matches every possible combination of two files, so it's
    lengthy and scales with O(n^2), so use with care with larger number of files. pass quick=True to only do one pair"""
    files = [directory_of_darks + file for file in listdir(directory_of_darks) if (file.lower().endswith(".fit") or file.lower().endswith("fits")) and not file.startswith("Master")]

    stdevs = []

    for i, file1 in enumerate(files):
        f1 = fits.open(file1)

        for j, file2 in enumerate(files):
            if file1 == file2:
                continue
            print(f"Matching file {i} with file {j}. {int(((i) * len(files) + (j)) / len(files)**2 * 100)}% done")

            f2 = fits.open(file2)

            stdevs.append(np.std(np.array(f1[0].data, dtype=int) - np.array(f2[0].data, dtype=int)))

            if quick:
                return stdevs[0]
    return np.median(stdevs)


if __name__=="__main__":
    print(get_dark_noise("C:/Users/ole/OneDrive/Desktop/Jufo/Daten/Darks5s/"))

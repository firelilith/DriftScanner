import numpy as np
from skimage.feature import peak_local_max
import matplotlib.pyplot as plt


def detect_stars(data_image, threshold_abs, min_separation=20, scan_length=100, scan_diameter=15):
    """Takes and image and finds local maxima, returns points and checks if drift line needs to be flipped for analyzer to work"""
    xy = peak_local_max(data_image, min_distance=min_separation, threshold_abs=threshold_abs)
    y, x = [i[0] for i in xy], [i[1] for i in xy]

    points = list(zip(y, x))

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

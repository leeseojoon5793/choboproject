import numpy as np
import pytest

from algorithms.otsu import manual_threshold, otsu, otsu_value


def two_level_image():
    img = np.full((40, 40), 40, np.uint8)
    img[:, 20:] = 200
    return img


def test_threshold_between_two_levels():
    t = otsu_value(two_level_image())
    assert 40 <= t < 200


def test_bright_side_becomes_white():
    out = otsu(two_level_image())
    assert out[0, 0] == 0 and out[0, 39] == 255


def test_invert_makes_dark_side_white():
    out = otsu(two_level_image(), invert=True)
    assert out[0, 0] == 255 and out[0, 39] == 0


def test_original_not_changed():
    img = two_level_image()
    before = img.copy()
    otsu(img)
    assert np.array_equal(img, before)


def test_color_image_rejected():
    with pytest.raises(ValueError):
        otsu(np.zeros((10, 10, 3), np.uint8))


def test_manual_threshold():
    out = manual_threshold(two_level_image(), 100)
    assert out[0, 0] == 0 and out[0, 39] == 255
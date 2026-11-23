import numpy as np

from algorithms.quality import brightness, contrast, sharpness


def test_brightness():
    img = np.array([[100, 100], [100, 100]], dtype=np.uint8)
    assert brightness(img) == 100.0


def test_contrast():
    img = np.array([[0, 100], [200, 255]], dtype=np.uint8)
    assert contrast(img) > 0


def test_sharpness():
    img = np.zeros((5, 5), dtype=np.uint8)
    img[2, 2] = 255
    assert sharpness(img) > 0
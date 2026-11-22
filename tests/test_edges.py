import numpy as np
import pytest

from algorithms.edges import sobel, canny


def test_sobel():
    img = np.zeros((10, 10), dtype=np.uint8)
    img[3:7, 3:7] = 255

    result = sobel(img)

    assert isinstance(result, np.ndarray)
    assert result.shape == img.shape
    assert result.dtype == np.uint8
    assert np.any(result > 0)


def test_canny():
    img = np.zeros((10, 10), dtype=np.uint8)
    img[3:7, 3:7] = 255

    result = canny(img)

    assert isinstance(result, np.ndarray)
    assert result.shape == img.shape
    assert result.dtype == np.uint8
    assert np.any(result > 0)


def test_sobel_invalid_image():
    img = np.zeros((10, 10, 3), dtype=np.uint8)

    with pytest.raises(ValueError):
        sobel(img)


def test_canny_invalid_image():
    img = np.zeros((10, 10, 3), dtype=np.uint8)

    with pytest.raises(ValueError):
        canny(img)


def test_canny_invalid_threshold():
    img = np.zeros((10, 10), dtype=np.uint8)

    with pytest.raises(ValueError):
        canny(img, 200, 100)
@pytest.mark.parametrize("invalid_value", ["100", True, False, float("nan")])
@pytest.mark.parametrize("position", [1, 2])
def test_canny_invalid_threshold_type(invalid_value, position):
    img = np.zeros((10, 10), dtype=np.uint8)

    thresholds = [100, 200]
    thresholds[position - 1] = invalid_value

    with pytest.raises(ValueError):
        canny(img, *thresholds)

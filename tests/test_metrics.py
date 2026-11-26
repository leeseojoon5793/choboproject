import math

import numpy as np
import pytest

from modules.metrics import psnr


def test_identical_images_give_infinity():
    a = np.full((4, 4), 100, dtype=np.uint8)
    assert psnr(a, a.copy()) == math.inf


def test_known_value_mse_1():
    # 모든 픽셀이 1씩 차이 → MSE = 1 → PSNR = 10·log10(255²)
    ref = np.zeros((2, 2), dtype=np.uint8)
    test = np.ones((2, 2), dtype=np.uint8)
    assert psnr(ref, test) == pytest.approx(10 * math.log10(255 ** 2))


def test_maximum_difference_gives_zero():
    # 0과 255로 정반대 → MSE = 255² → PSNR = 0
    ref = np.zeros((2, 2), dtype=np.uint8)
    test = np.full((2, 2), 255, dtype=np.uint8)
    assert psnr(ref, test) == pytest.approx(0.0)


def test_no_uint8_wraparound():
    # uint8 그대로 빼면 0 - 255가 1로 돌아가서 PSNR이 엉뚱하게 커짐
    ref = np.array([[0]], dtype=np.uint8)
    test = np.array([[255]], dtype=np.uint8)
    assert psnr(ref, test) == pytest.approx(0.0)


def test_order_does_not_matter():
    rng = np.random.default_rng(0)
    a = rng.integers(0, 256, (8, 8), dtype=np.uint8)
    b = rng.integers(0, 256, (8, 8), dtype=np.uint8)
    assert psnr(a, b) == pytest.approx(psnr(b, a))


def test_more_noise_lower_psnr():
    rng = np.random.default_rng(1)
    ref = np.full((32, 32), 128, dtype=np.uint8)
    small = np.clip(ref + rng.normal(0, 5, ref.shape), 0, 255).astype(np.uint8)
    large = np.clip(ref + rng.normal(0, 30, ref.shape), 0, 255).astype(np.uint8)
    assert psnr(ref, small) > psnr(ref, large)


def test_inputs_not_modified():
    ref = np.zeros((3, 3), dtype=np.uint8)
    test = np.full((3, 3), 10, dtype=np.uint8)
    r0, t0 = ref.copy(), test.copy()
    psnr(ref, test)
    assert np.array_equal(ref, r0) and np.array_equal(test, t0)


def test_different_shapes_rejected():
    with pytest.raises(ValueError, match="크기가 같아야"):
        psnr(np.zeros((2, 2), np.uint8), np.zeros((2, 3), np.uint8))


@pytest.mark.parametrize("bad", [np.zeros((2, 2), np.float32), np.zeros((2, 2, 3), np.uint8)])
def test_wrong_type_rejected(bad):
    with pytest.raises(ValueError, match="uint8"):
        psnr(bad, bad.copy())

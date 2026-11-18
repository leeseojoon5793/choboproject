import numpy as np
import pytest

from algorithms.filters import bilateral_filter, gaussian_filter, median_filter

ALL_FILTERS = [median_filter, gaussian_filter, bilateral_filter]


def salt_image():
    # 검은 바탕 한가운데 하얀 점 하나 (튀는 잡음 흉내)
    img = np.zeros((9, 9), dtype=np.uint8)
    img[4, 4] = 255
    return img


def step_image():
    # 왼쪽 절반 0, 오른쪽 절반 200인 선명한 경계
    img = np.zeros((20, 20), dtype=np.uint8)
    img[:, 10:] = 200
    return img


# ---------- 공통 규칙 ----------

@pytest.mark.parametrize("f", ALL_FILTERS)
def test_returns_new_array_same_shape(f):
    img = salt_image()
    before = img.copy()
    out = f(img)
    assert out.shape == img.shape
    assert out.dtype == np.uint8
    assert out is not img
    assert np.array_equal(img, before)  # 원본 그대로


@pytest.mark.parametrize("f", ALL_FILTERS)
def test_flat_image_stays_flat(f):
    flat = np.full((15, 15), 120, dtype=np.uint8)
    assert np.all(f(flat) == 120)


@pytest.mark.parametrize("f", ALL_FILTERS)
def test_color_image_rejected(f):
    with pytest.raises(ValueError, match="2차원"):
        f(np.zeros((5, 5, 3), dtype=np.uint8))


@pytest.mark.parametrize("f", ALL_FILTERS)
def test_non_uint8_rejected(f):
    with pytest.raises(ValueError, match="uint8"):
        f(np.zeros((5, 5), dtype=np.float32))


# ---------- 파라미터 검사 ----------

@pytest.mark.parametrize("f", [median_filter, gaussian_filter])
@pytest.mark.parametrize("ksize, reason", [(4, "홀수"), (1, "홀수"), (0, "홀수"), (3.0, "정수"), (True, "정수")])
def test_bad_ksize_rejected(f, ksize, reason):
    with pytest.raises(ValueError, match=reason):
        f(salt_image(), ksize=ksize)


def test_gaussian_negative_sigma_rejected():
    with pytest.raises(ValueError, match="sigma"):
        gaussian_filter(salt_image(), sigma=-1)


@pytest.mark.parametrize("params", [{"d": 0}, {"d": 2.5}, {"sigma_color": 0}, {"sigma_space": -5}])
def test_bilateral_bad_params_rejected(params):
    with pytest.raises(ValueError):
        bilateral_filter(salt_image(), **params)


# ---------- 필터마다 성격 차이 ----------

def test_median_removes_single_bright_dot():
    out = median_filter(salt_image(), ksize=3)
    assert out.max() == 0  # 튀는 점이 완전히 사라짐

def test_median_removes_single_dark_dot():
    img = np.full((9, 9), 200, dtype=np.uint8)
    img[4, 4] = 0
    out = median_filter(img, ksize=3)
    assert out.min() == 200 # 검은 점이 사라지고 전부 200
    
def test_gaussian_spreads_single_bright_dot():
    out = gaussian_filter(salt_image(), ksize=3)
    assert 0 < out[4, 4] < 255  # 점이 흐려지고
    assert out[4, 3] > 0        # 옆으로 번짐


def test_bilateral_keeps_edge_sharper_than_gaussian():
    img = step_image().astype(np.int32)
    bil = bilateral_filter(step_image(), d=9, sigma_color=30, sigma_space=75).astype(np.int32)
    gau = gaussian_filter(step_image(), ksize=9).astype(np.int32)
    # 원본에서 얼마나 달라졌나: 경계를 지킬수록 작다
    assert np.abs(bil - img).max() < np.abs(gau - img).max()

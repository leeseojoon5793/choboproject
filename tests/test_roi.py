import numpy as np
import pytest

from modules.roi import crop_roi, roi_histogram, roi_stats, validate_roi


@pytest.fixture
def img():
    # 높이 4, 폭 5짜리 테스트 영상. 값 = 행 * 10 + 열 이라 위치를 쉽게 알 수 있다.
    return np.array([[r * 10 + c for c in range(5)] for r in range(4)], dtype=np.uint8)


# ---------- 잘못된 ROI 거절 ----------

@pytest.mark.parametrize(
    "roi, reason",
    [
        ({"x": 0, "y": 0, "w": 0, "h": 2}, "폭과 높이"),
        ({"x": 0, "y": 0, "w": 2, "h": -1}, "폭과 높이"),
        ({"x": -1, "y": 0, "w": 2, "h": 2}, "시작 좌표"),
        ({"x": 4, "y": 0, "w": 2, "h": 2}, "범위를 벗어납니다"),
        ({"x": 0, "y": 3, "w": 2, "h": 2}, "범위를 벗어납니다"),
        ({"x": 0, "y": 0, "w": 2}, "h 값이 없습니다"),
        ({"x": 0.5, "y": 0, "w": 2, "h": 2}, "정수"),
        ({"x": True, "y": 0, "w": 2, "h": 2}, "정수"),
    ],
)
def test_invalid_roi_rejected_with_reason(img, roi, reason):
    with pytest.raises(ValueError, match=reason):
        validate_roi(roi, img.shape)


def test_color_image_rejected():
    color = np.zeros((4, 5, 3), dtype=np.uint8)
    with pytest.raises(ValueError, match="2차원"):
        validate_roi({"x": 0, "y": 0, "w": 1, "h": 1}, color.shape)


def test_roi_touching_edge_is_valid(img):
    validate_roi({"x": 3, "y": 2, "w": 2, "h": 2}, img.shape)  # 오른쪽 아래 끝까지 딱 맞음


def test_numpy_int_coordinates_accepted(img):
    validate_roi({"x": np.int64(1), "y": 0, "w": 2, "h": 2}, img.shape)


# ---------- 자르기 ----------

def test_crop_takes_correct_region(img):
    region = crop_roi(img, {"x": 1, "y": 2, "w": 3, "h": 1})
    assert region.tolist() == [[21, 22, 23]]


def test_crop_does_not_modify_original(img):
    before = img.copy()
    region = crop_roi(img, {"x": 0, "y": 0, "w": 2, "h": 2})
    region[:] = 255
    assert np.array_equal(img, before)


# ---------- 통계 ----------

def test_stats_constant_region():
    flat = np.full((10, 10), 80, dtype=np.uint8)
    s = roi_stats(flat, {"x": 2, "y": 2, "w": 5, "h": 5})
    assert s["mean"] == 80
    assert s["var"] == 0
    assert s["count"] == 25


def test_stats_known_values(img):
    # 값 10, 11, 20, 21 → 평균 15.5, 모분산 = (5.5²+4.5²+4.5²+5.5²)/4 = 25.25
    s = roi_stats(img, {"x": 0, "y": 1, "w": 2, "h": 2})
    assert s["mean"] == pytest.approx(15.5)
    assert s["var"] == pytest.approx(25.25)
    assert s["std"] == pytest.approx(25.25 ** 0.5)


def test_stats_with_extreme_values():
    # 0과 255처럼 극단값이 섞여 있어도 평균﹒분산이 정확한지 확인
    bright = np.array([[0, 255], [255, 0]], dtype=np.uint8)
    s = roi_stats(bright, {"x": 0, "y": 0, "w": 2, "h": 2})
    assert s["mean"] == pytest.approx(127.5)
    assert s["var"] == pytest.approx(127.5 ** 2)


# ---------- 히스토그램 ----------

def test_histogram_counts_sum_to_pixel_count(img):
    counts, edges = roi_histogram(img, {"x": 0, "y": 0, "w": 5, "h": 4})
    assert counts.sum() == 20
    assert len(counts) == 256
    assert len(edges) == 257


def test_histogram_puts_values_in_right_bins():
    a = np.array([[0, 0, 255]], dtype=np.uint8)
    counts, _ = roi_histogram(a, {"x": 0, "y": 0, "w": 3, "h": 1})
    assert counts[0] == 2
    assert counts[255] == 1

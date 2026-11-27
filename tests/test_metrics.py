import math

import numpy as np
import pytest

from modules.metrics import compare_quality, edge_contrast, noise_level, psnr


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


# ---------- 추천 기능용 지표 (noise_level, edge_contrast, compare_quality) ----------


FLAT = {"x": 0, "y": 0, "w": 4, "h": 4}
LESION = {"x": 0, "y": 0, "w": 2, "h": 2}
BACKGROUND = {"x": 2, "y": 0, "w": 2, "h": 2}


def test_noise_level_is_std_of_flat_roi():
    img = np.array([[10, 30], [10, 30]], dtype=np.uint8)
    assert noise_level(img, {"x": 0, "y": 0, "w": 2, "h": 2}) == pytest.approx(10.0)


def test_noise_level_zero_for_uniform_region():
    img = np.full((4, 4), 80, dtype=np.uint8)
    assert noise_level(img, FLAT) == 0


def test_edge_contrast_is_mean_difference():
    img = np.zeros((2, 4), dtype=np.uint8)
    img[:, 2:] = 200  # 왼쪽(병변) 0, 오른쪽(주변) 200
    assert edge_contrast(img, LESION, BACKGROUND) == pytest.approx(200.0)


def test_edge_contrast_order_does_not_matter():
    img = np.zeros((2, 4), dtype=np.uint8)
    img[:, 2:] = 200
    assert edge_contrast(img, BACKGROUND, LESION) == pytest.approx(200.0)


def test_bad_roi_reason_passes_through():
    img = np.zeros((4, 4), dtype=np.uint8)
    with pytest.raises(ValueError, match="범위를 벗어납니다"):
        noise_level(img, {"x": 3, "y": 0, "w": 4, "h": 1})


def _noisy_and_smoothed():
    # 왼쪽 2열(병변)은 평균 50, 오른쪽 2열(주변)은 평균 200. 각 영역 안에 ±10 흔들림
    before = np.array([
        [40, 60, 190, 210],
        [60, 40, 210, 190],
        [40, 60, 190, 210],
        [60, 40, 210, 190],
    ], dtype=np.uint8)
    # 흔들림만 없앤 영상 (평균은 그대로)
    after = np.array([
        [50, 50, 200, 200],
        [50, 50, 200, 200],
        [50, 50, 200, 200],
        [50, 50, 200, 200],
    ], dtype=np.uint8)
    return before, after


def test_compare_quality_perfect_smoothing():
    before, after = _noisy_and_smoothed()
    flat = {"x": 0, "y": 0, "w": 2, "h": 4}           # 병변 안쪽 (흔들림만 있는 부위)
    lesion = {"x": 0, "y": 0, "w": 2, "h": 4}
    background = {"x": 2, "y": 0, "w": 2, "h": 4}
    q = compare_quality(before, after, flat, lesion, background)
    assert q["noise_before"] == pytest.approx(10.0)
    assert q["noise_after"] == 0
    assert q["noise_reduction"] == pytest.approx(1.0)      # 잡음 100% 감소
    assert q["edge_preservation"] == pytest.approx(1.0)    # 테두리 그대로


def test_compare_quality_no_change():
    before, _ = _noisy_and_smoothed()
    flat = {"x": 0, "y": 0, "w": 2, "h": 4}
    q = compare_quality(before, before.copy(), flat, {"x": 0, "y": 0, "w": 2, "h": 4}, {"x": 2, "y": 0, "w": 2, "h": 4})
    assert q["noise_reduction"] == pytest.approx(0.0)
    assert q["edge_preservation"] == pytest.approx(1.0)


def test_compare_quality_blurred_edge_lowers_preservation():
    before, _ = _noisy_and_smoothed()
    blurred = np.full((4, 4), 125, dtype=np.uint8)  # 너무 세게 뭉개서 병변과 주변이 같아짐
    flat = {"x": 0, "y": 0, "w": 2, "h": 4}
    q = compare_quality(before, blurred, flat, {"x": 0, "y": 0, "w": 2, "h": 4}, {"x": 2, "y": 0, "w": 2, "h": 4})
    assert q["noise_reduction"] == pytest.approx(1.0)      # 잡음은 다 없어졌지만
    assert q["edge_preservation"] == pytest.approx(0.0)    # 테두리도 사라짐


def test_compare_quality_rejects_uniform_flat_roi():
    img = np.full((4, 4), 80, dtype=np.uint8)
    img[:, 2:] = 200
    with pytest.raises(ValueError, match="잡음 감소"):
        compare_quality(img, img.copy(), {"x": 0, "y": 0, "w": 2, "h": 4}, LESION, BACKGROUND)


def test_compare_quality_rejects_equal_lesion_and_background():
    before, _ = _noisy_and_smoothed()
    same = {"x": 0, "y": 0, "w": 2, "h": 2}
    with pytest.raises(ValueError, match="테두리 보존"):
        compare_quality(before, before.copy(), {"x": 0, "y": 0, "w": 2, "h": 4}, same, same)


def test_compare_quality_rejects_different_shapes():
    before, _ = _noisy_and_smoothed()
    with pytest.raises(ValueError, match="크기가 같아야"):
        compare_quality(before, np.zeros((5, 5), np.uint8), FLAT, LESION, BACKGROUND)


def test_compare_quality_does_not_modify_inputs():
    before, after = _noisy_and_smoothed()
    b0, a0 = before.copy(), after.copy()
    compare_quality(before, after, {"x": 0, "y": 0, "w": 2, "h": 4}, {"x": 0, "y": 0, "w": 2, "h": 4}, {"x": 2, "y": 0, "w": 2, "h": 4})
    assert np.array_equal(before, b0) and np.array_equal(after, a0)

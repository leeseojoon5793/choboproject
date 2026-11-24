import numpy as np
import pytest
from algorithms.clahe import apply_clahe


def test_apply_clahe_uint8_shape_and_dtype():
    img = np.linspace(50, 200, 64 * 64, dtype=np.uint8).reshape(64, 64)
    result = apply_clahe(img, clip_limit=2.0, tile_grid_size=(8, 8))
    assert result.shape == img.shape
    assert result.dtype == np.uint8


def test_apply_clahe_float_shape_and_dtype():
    img = np.linspace(0.2, 0.8, 64 * 64, dtype=np.float32).reshape(64, 64)
    result = apply_clahe(img)
    assert result.shape == img.shape
    assert result.dtype == np.float32
    assert 0.0 <= result.min() <= result.max() <= 1.0


def test_apply_clahe_enhances_low_contrast():
    # 대비가 매우 낮은 이미지 생성
    rng = np.random.default_rng(42)
    img = rng.integers(100, 110, size=(64, 64), dtype=np.uint8)
    result = apply_clahe(img, clip_limit=3.0)
    assert result.std() > img.std()


def test_apply_clahe_invalid_inputs():
    with pytest.raises(ValueError):
        apply_clahe(np.zeros((32, 32, 3), dtype=np.uint8))  # 3D 컬러 이미지
    with pytest.raises(ValueError):
        apply_clahe(np.zeros((32, 32), dtype=np.uint8), clip_limit=0)
    with pytest.raises(ValueError):
        apply_clahe(np.zeros((32, 32), dtype=np.uint8), tile_grid_size=(0, 8))

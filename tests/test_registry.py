import numpy as np
import pytest

from algorithms.registry import ALGORITHMS, default_params, run_algorithm


def sample_image():
    rng = np.random.default_rng(0)
    return rng.integers(0, 256, size=(32, 32), dtype=np.uint8)


# ---------- 등록 목록 자체 검사 (팀원이 새로 추가해도 자동으로 검사됨) ----------

@pytest.mark.parametrize("key", list(ALGORITHMS))
def test_registry_entry_is_well_formed(key):
    algo = ALGORITHMS[key]
    assert {"label", "func", "version", "params"} <= set(algo)
    for name, spec in algo["params"].items():
        assert {"min", "max", "step", "default"} <= set(spec), name
        assert spec["min"] <= spec["default"] <= spec["max"], name
        assert spec["step"] > 0, name


@pytest.mark.parametrize("key", list(ALGORITHMS))
def test_every_algorithm_runs_with_defaults(key):
    img = sample_image()
    before = img.copy()
    out = run_algorithm(key, img)
    assert isinstance(out, np.ndarray)
    assert out.shape == img.shape
    assert np.array_equal(img, before)  # 원본 그대로


# ---------- 실행 ----------

def test_given_params_are_used():
    img = sample_image()
    expected = ALGORITHMS["median"]["func"](img, ksize=5)
    assert np.array_equal(run_algorithm("median", img, {"ksize": 5}), expected)


def test_missing_params_filled_with_defaults():
    assert default_params("bilateral") == {"d": 9, "sigma_color": 75, "sigma_space": 75}
    img = sample_image()
    partial = run_algorithm("bilateral", img, {"d": 5})
    full = run_algorithm("bilateral", img, {"d": 5, "sigma_color": 75, "sigma_space": 75})
    assert np.array_equal(partial, full)


# ---------- 거절 ----------

def test_unknown_algorithm_rejected():
    with pytest.raises(ValueError, match="등록되지 않은"):
        run_algorithm("magic", sample_image())


def test_unknown_param_rejected():
    with pytest.raises(ValueError, match="없는 파라미터"):
        run_algorithm("median", sample_image(), {"sigma": 3})


@pytest.mark.parametrize("value", [1, 17])
def test_out_of_range_param_rejected(value):
    with pytest.raises(ValueError, match="사이여야"):
        run_algorithm("median", sample_image(), {"ksize": value})

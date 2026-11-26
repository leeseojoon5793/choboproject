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

# ---------- 자료형 검사 (리뷰 반영) ----------

@pytest.mark.parametrize("bad_params", [[("ksize", 3)], "ksize=3", 3])
def test_params_must_be_dict(bad_params):
    with pytest.raises(ValueError, match="딕셔너리"):
        run_algorithm("median", sample_image(), bad_params)


@pytest.mark.parametrize("key, params", [
    ("bilateral", {"sigma_color": True}),
    ("median", {"ksize": "3"}),
    ("median", {"ksize": None}),
])
def test_non_number_param_rejected(key, params):
    with pytest.raises(ValueError, match="숫자"):
        run_algorithm(key, sample_image(), params)


@pytest.mark.parametrize("value", [3.5, 5.0])
def test_float_for_int_param_rejected(value):
    with pytest.raises(ValueError, match="정수"):
        run_algorithm("median", sample_image(), {"ksize": value})


def test_nan_param_rejected():
    # sigma_color는 정수 슬라이더라 NaN(소수)은 "정수여야"로 거절된다
    with pytest.raises(ValueError, match="정수"):
        run_algorithm("bilateral", sample_image(), {"sigma_color": float("nan")})


def test_numpy_int_param_accepted():
    run_algorithm("median", sample_image(), {"ksize": np.int64(5)})
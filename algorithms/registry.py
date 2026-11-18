"""알고리즘 실행 틀.

화면은 이 목록(ALGORITHMS)을 읽어서 알고리즘 선택 상자와 파라미터 슬라이더를 만든다.
새 알고리즘을 붙이려면 함수를 만든 뒤 아래 ALGORITHMS에 한 칸만 추가하면 된다.

파라미터 정보: {"min", "max", "step", "default"}
- 네 값이 모두 int면 정수 슬라이더, 하나라도 float면 실수 슬라이더
- 홀수만 받는 커널은 min을 홀수로, step을 2로 두면 슬라이더에서 홀수만 나온다
"""
import numpy as np

from algorithms.filters import bilateral_filter, gaussian_filter, median_filter

ALGORITHMS = {
    "median": {
        "label": "Median 필터 (노이즈 제거)",
        "func": median_filter,
        "version": "1.0",
        "params": {
            "ksize": {"min": 3, "max": 15, "step": 2, "default": 3},
        },
    },
    "bilateral": {
        "label": "Bilateral 필터 (노이즈 제거, 경계 보존)",
        "func": bilateral_filter,
        "version": "1.0",
        "params": {
            "d": {"min": 1, "max": 15, "step": 1, "default": 9},
            "sigma_color": {"min": 1, "max": 150, "step": 1, "default": 75},
            "sigma_space": {"min": 1, "max": 150, "step": 1, "default": 75},
        },
    },
    "gaussian": {
        "label": "Gaussian 필터 (비교 기준)",
        "func": gaussian_filter,
        "version": "1.0",
        "params": {
            "ksize": {"min": 3, "max": 15, "step": 2, "default": 5},
        },
    },
    # 다른 팀원 알고리즘은 여기에 같은 모양으로 추가
}


def _get(key: str) -> dict:
    if key not in ALGORITHMS:
        raise ValueError(f"등록되지 않은 알고리즘입니다: {key}")
    return ALGORITHMS[key]


def default_params(key: str) -> dict:
    """알고리즘의 파라미터 기본값을 {이름: 기본값} 딕셔너리로 돌려준다."""
    result = {}
    for name, spec in _get(key)["params"].items():
        result[name] = spec["default"]
    return result


def run_algorithm(key: str, img: np.ndarray, params: dict | None = None) -> np.ndarray:
    """알고리즘을 찾아서 파라미터를 검사한 뒤 실행한다. 빠진 파라미터는 기본값으로 채운다."""
    algo = _get(key)
    specs = algo["params"]
    params = params or {}

    unknown = set(params) - set(specs)
    if unknown:
        raise ValueError(f"{algo['label']}에 없는 파라미터입니다: {', '.join(sorted(unknown))}")

    merged = default_params(key)
    merged.update(params)
    for name, value in merged.items():
        spec = specs[name]
        if not spec["min"] <= value <=spec["max"]:
            raise ValueError(f"{name} 값은 {spec['min']}~{spec['max']} 사이여야 합니다.")

    return algo["func"](img, **merged)

    

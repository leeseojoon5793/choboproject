"""화질 지표 (역할 C)."""
import numpy as np


def psnr(reference: np.ndarray, test: np.ndarray) -> float:
    """정답 영상(reference)과 비교한 PSNR(dB). 클수록 정답에 가깝다. 두 영상이 같으면 inf."""
    if reference.shape != test.shape:
        raise ValueError("두 영상의 크기가 같아야 합니다.")
    if reference.ndim != 2 or reference.dtype != np.uint8 or test.dtype != np.uint8:
        raise ValueError("8비트 흑백(2차원 uint8) 영상만 지원합니다.")
    diff = reference.astype(np.float64) - test.astype(np.float64)
    mse = np.mean(diff ** 2)
    if mse == 0:
        return float("inf")
    return float(10 * np.log10(255 ** 2 / mse))

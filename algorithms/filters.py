"""CT 저선량 잡음 제거용 필터 (역할 C).

- median_filter: 주변 값의 가운데 값으로 바꿈. 튀는 점 제거에 강하고 경계가 덜 뭉개짐
- bilateral_filter: 거리도 가깝고 밝기도 비슷한 이웃만 섞음. 경계를 지키면서 평평한 곳을 매끈하게
- gaussian_filter: 주변 값을 가까울수록 크게 가중 평균. 비교 기준용

모든 함수는 팀 공통 형태 (img, **params) -> 새 배열 이고, 원본은 바꾸지 않는다.
입력은 8비트 흑백(2차원 uint8) 영상만 받는다.
"""
import cv2
import numpy as np


def _check_image(img: np.ndarray) -> None:
    if not isinstance(img, np.ndarray) or img.ndim != 2:
        raise ValueError("흑백(2차원) 영상만 지원합니다.")
    if img.dtype != np.uint8:
        raise ValueError("8비트(uint8) 영상만 지원합니다.")


def _check_odd_ksize(ksize, minimum: int = 3) -> None:
    if isinstance(ksize, bool) or not isinstance(ksize, (int, np.integer)):
        raise ValueError("커널 크기는 정수여야 합니다.")
    if ksize < minimum or ksize % 2 == 0:
        raise ValueError(f"커널 크기는 {minimum} 이상의 홀수여야 합니다.")


def median_filter(img: np.ndarray, ksize: int = 3) -> np.ndarray:
    _check_image(img)
    _check_odd_ksize(ksize)
    return cv2.medianBlur(img, ksize)


def gaussian_filter(img: np.ndarray, ksize: int = 5, sigma: float = 0) -> np.ndarray:
    """sigma가 0이면 OpenCV가 커널 크기로부터 자동 계산한다."""
    _check_image(img)
    _check_odd_ksize(ksize)
    if sigma < 0:
        raise ValueError("sigma는 0 이상이어야 합니다.")
    return cv2.GaussianBlur(img, (ksize, ksize), sigma)


def bilateral_filter(
    img: np.ndarray, d: int = 9, sigma_color: float = 75, sigma_space: float = 75
) -> np.ndarray:
    """d: 이웃 범위(지름), sigma_color: 밝기 차이를 얼마나 봐줄지, sigma_space: 거리를 얼마나 봐줄지.

    기본값은 출발점일 뿐이고, 초음파에 맞는 값은 비교 실험으로 정한다.
    """
    _check_image(img)
    if isinstance(d, bool) or not isinstance(d, (int, np.integer)) or d < 1:
        raise ValueError("d는 1 이상의 정수여야 합니다.")
    if sigma_color <= 0 or sigma_space <= 0:
        raise ValueError("sigma_color와 sigma_space는 0보다 커야 합니다.")
    return cv2.bilateralFilter(img, d, sigma_color, sigma_space)

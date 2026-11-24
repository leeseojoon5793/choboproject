import numpy as np
import cv2


def validate_image(img: np.ndarray):
    if not isinstance(img, np.ndarray):
        raise TypeError("입력은 numpy 배열이어야 합니다.")

    if img.ndim != 2:
        raise ValueError("입력 영상은 2차원 흑백 영상이어야 합니다.")

    if img.dtype != np.uint8:
        raise ValueError("입력 영상은 uint8 형식이어야 합니다.")


def sobel(img: np.ndarray) -> np.ndarray:
    validate_image(img)

    grad_x = cv2.Sobel(img, cv2.CV_64F, 1, 0, ksize=3)
    grad_y = cv2.Sobel(img, cv2.CV_64F, 0, 1, ksize=3)

    magnitude = cv2.magnitude(grad_x, grad_y)

    return cv2.convertScaleAbs(magnitude)


def canny(
    img: np.ndarray,
    threshold1: int = 100,
    threshold2: int = 200
) -> np.ndarray:
    validate_image(img)

    for threshold in (threshold1, threshold2):
        if (
            isinstance(threshold, (bool, np.bool_))
            or not isinstance(threshold, (int, float, np.integer, np.floating))
            or not np.isfinite(threshold)
        ):
            raise ValueError("임계값은 유효한 숫자여야 합니다.")

    if not (0 <= threshold1 < threshold2 <= 255):
        raise ValueError("임계값은 0 이상 255 이하이며 threshold1이 더 작아야 합니다.")

    return cv2.Canny(img, threshold1, threshold2)

import numpy as np
import cv2


def validate_image(img: np.ndarray):
    if not isinstance(img, np.ndarray):
        raise TypeError("입력은 numpy 배열이어야 합니다.")

    if img.ndim != 2:
        raise ValueError("입력 영상은 2차원 흑백 영상이어야 합니다.")

    if img.dtype != np.uint8:
        raise ValueError("입력 영상은 uint8 형식이어야 합니다.")


def brightness(img: np.ndarray) -> float:
    validate_image(img)
    return float(np.mean(img))


def contrast(img: np.ndarray) -> float:
    validate_image(img)
    return float(np.std(img))


def sharpness(img: np.ndarray) -> float:
    validate_image(img)
    return float(cv2.Laplacian(img, cv2.CV_64F).var())
import cv2
import numpy as np


def _flag(invert):
    return cv2.THRESH_BINARY_INV if invert else cv2.THRESH_BINARY


def otsu_value(img: np.ndarray) -> float:
    t, _ = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    return t


def otsu(img: np.ndarray, invert: bool = False) -> np.ndarray:
    # Otsu는 8비트 흑백에서만 동작
    if img.ndim != 2 or img.dtype != np.uint8:
        raise ValueError("8비트 흑백 영상만 처리할 수 있습니다.")
    _, out = cv2.threshold(img, 0, 255, _flag(invert) | cv2.THRESH_OTSU)
    return out


def manual_threshold(img: np.ndarray, t: int, invert: bool = False) -> np.ndarray:
    _, out = cv2.threshold(img, t, 255, _flag(invert))
    return out
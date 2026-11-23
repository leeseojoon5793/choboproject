import cv2
import numpy as np


def apply_clahe(
    image: np.ndarray,
    clip_limit: float = 2.0,
    tile_grid_size: tuple[int, int] = (8, 8),
) -> np.ndarray:
    """2D 그레이스케일 이미지에 CLAHE(Contrast Limited Adaptive Histogram Equalization)를 적용한다."""
    if not isinstance(image, np.ndarray):
        raise TypeError("입력 이미지는 numpy.ndarray여야 합니다.")
    if image.ndim != 2:
        raise ValueError(f"2D 그레이스케일 이미지만 지원합니다. (현재 차원: {image.ndim})")
    if image.size == 0:
        raise ValueError("빈 이미지는 처리할 수 없습니다.")
    if clip_limit <= 0:
        raise ValueError("clip_limit는 0보다 커야 합니다.")
    if (
        len(tile_grid_size) != 2
        or tile_grid_size[0] <= 0
        or tile_grid_size[1] <= 0
    ):
        raise ValueError("tile_grid_size는 양의 정수 2개 튜플이어야 합니다.")

    orig_dtype = image.dtype

    # float 타입(0.0 ~ 1.0) 입력 시 uint8로 변환 후 복원
    if np.issubdtype(orig_dtype, np.floating):
        img_uint8 = np.clip(image * 255.0, 0, 255).astype(np.uint8)
        clahe = cv2.createCLAHE(clipLimit=float(clip_limit), tileGridSize=tuple(tile_grid_size))
        enhanced = clahe.apply(img_uint8)
        return (enhanced.astype(np.float32) / 255.0).astype(orig_dtype)

    if orig_dtype != np.uint8:
        raise TypeError(f"지원하지 않는 이미지 dtype입니다: {orig_dtype} (uint8 또는 float 지원)")

    clahe = cv2.createCLAHE(clipLimit=float(clip_limit), tileGridSize=tuple(tile_grid_size))
    return clahe.apply(image)

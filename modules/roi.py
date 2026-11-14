"""ROI(관심 영역) 검사와 통계 계산.

ROI 형식: {"x": 열, "y": 행, "w": 폭, "h": 높이}
픽셀 단위이고 원점(0, 0)은 영상 왼쪽 위.
"""
import numpy as np

ROI_KEYS = ("x", "y", "w", "h")


def validate_roi(roi: dict, image_shape: tuple) -> None:
    """ROI가 영상 안에 제대로 들어가는지 검사한다. 문제가 있으면 이유를 담아 ValueError를 낸다."""
    if len(image_shape) != 2:
        raise ValueError("흑백(2차원) 영상만 지원합니다.")

    missing = [k for k in ROI_KEYS if k not in roi]
    if missing:
        raise ValueError(f"ROI에 {', '.join(missing)} 값이 없습니다.")

    for k in ROI_KEYS:
        v = roi[k]
        # bool은 int의 하위 타입이라 따로 막는다 (True가 1로 통과하는 것 방지)
        if isinstance(v, bool) or not isinstance(v, (int, np.integer)):
            raise ValueError(f"ROI의 {k} 값은 정수여야 합니다.")

    x, y, w, h = (int(roi[k]) for k in ROI_KEYS)
    height, width = image_shape

    if w <= 0 or h <= 0:
        raise ValueError("ROI의 폭과 높이는 1 이상이어야 합니다.")
    if x < 0 or y < 0:
        raise ValueError("ROI의 시작 좌표는 0 이상이어야 합니다.")
    if x + w > width or y + h > height:
        raise ValueError(
            f"ROI가 영상 범위를 벗어납니다. (영상 크기: 폭 {width}, 높이 {height})"
        )


def crop_roi(img: np.ndarray, roi: dict) -> np.ndarray:
    """ROI 부분만 잘라서 복사본으로 돌려준다. 원본은 건드리지 않는다."""
    validate_roi(roi, img.shape)
    x, y, w, h = (int(roi[k]) for k in ROI_KEYS)
    return img[y:y + h, x:x + w].copy()


def roi_stats(img: np.ndarray, roi: dict) -> dict:
    """ROI의 평균, 분산, 표준편차, 픽셀 수를 계산한다. 분산은 모분산(N으로 나눔)."""
    region = crop_roi(img, roi).astype(np.float64)
    return {
        "mean": float(region.mean()),
        "var": float(region.var()),
        "std": float(region.std()),
        "count": int(region.size),
    }


def roi_histogram(img: np.ndarray, roi: dict, bins: int = 256) -> tuple:
    """ROI의 밝기 히스토그램. 8비트 영상 기준으로 0~255 범위를 bins개 구간으로 나눈다.

    반환: (counts, edges) — np.histogram과 같은 형태
    """
    region = crop_roi(img, roi)
    return np.histogram(region, bins=bins, range=(0, 256))

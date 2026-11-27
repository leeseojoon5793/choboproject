"""화질 지표 (역할 C)."""
import numpy as np
from modules.roi import roi_stats


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

def noise_level(img: np.ndarray, flat_roi: dict) -> float:
    """평평한 부위 ROI의 표준편차. 작을수록 매끈하다(잡음이 적다)."""
    return roi_stats(img, flat_roi)["std"]


def edge_contrast(img: np.ndarray, lesion_roi: dict, background_roi: dict) -> float:
    """병변 ROI와 주변 ROI의 평균 밝기 차이(절댓값). 테두리가 뭉개지면 작아진다."""
    lesion_mean = roi_stats(img, lesion_roi)["mean"]
    background_mean = roi_stats(img, background_roi)["mean"]
    return abs(lesion_mean - background_mean)


def compare_quality(
    before: np.ndarray, after: np.ndarray,
    flat_roi: dict, lesion_roi: dict, background_roi: dict,
) -> dict:
    """같은 저선량 영상의 처리 전(before)·후(after)를 비교한다. 정답 없이 계산하는 추천용 지표.

    before는 저선량 입력 영상(처리 전)이다. 일반 선량 정답 영상을 넣지 말 것.
    정답과의 비교는 psnr()로 따로 하고, 검증 실험에서만 쓴다.

    noise_reduction: 1 - 후/전. 클수록 잡음이 많이 줄었다.
    edge_preservation: 후/전. 1에 가까울수록 테두리가 잘 남았다.
    """
    if before.shape != after.shape:
        raise ValueError("두 영상의 크기가 같아야 합니다.")

    noise_before = noise_level(before, flat_roi)
    noise_after = noise_level(after, flat_roi)
    contrast_before = edge_contrast(before, lesion_roi, background_roi)
    contrast_after = edge_contrast(after, lesion_roi, background_roi)

    if noise_before == 0:
        raise ValueError("평평한 부위 ROI에 밝기 변화가 없어 잡음 감소를 계산할 수 없습니다. ROI를 다시 잡아 주세요.")
    if contrast_before == 0:
        raise ValueError("병변과 주변 ROI의 밝기가 같아 테두리 보존을 계산할 수 없습니다. ROI를 다시 잡아 주세요.")

    return {
        "noise_before": noise_before,
        "noise_after": noise_after,
        "noise_reduction": 1 - noise_after / noise_before,
        "contrast_before": contrast_before,
        "contrast_after": contrast_after,
        "edge_preservation": contrast_after / contrast_before,
    }
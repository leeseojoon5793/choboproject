import cv2
import numpy as np

from modules.metrics import compare_quality


def validate_ksizes(ksizes):
    for ksize in ksizes:
        if not isinstance(ksize, int) or ksize < 3 or ksize % 2 == 0:
            raise ValueError("커널 크기는 3 이상의 홀수여야 합니다.")


def generate_candidates(
    median_ksizes=(3, 5, 7),
    gaussian_ksizes=(3, 5, 7),
    bilateral_d=9,
    bilateral_sigma_color=75,
    bilateral_sigma_space=75
):
    validate_ksizes(median_ksizes)
    validate_ksizes(gaussian_ksizes)

    if bilateral_d < 1:
        raise ValueError("Bilateral d는 1 이상이어야 합니다.")

    if bilateral_sigma_color <= 0 or bilateral_sigma_space <= 0:
        raise ValueError("Bilateral 강도 값은 0보다 커야 합니다.")

    candidates = []

    for ksize in median_ksizes:
        candidates.append({
            "이름": f"Median (ksize={ksize})",
            "filter": "median",
            "ksize": ksize
        })

    for ksize in gaussian_ksizes:
        candidates.append({
            "이름": f"Gaussian (ksize={ksize})",
            "filter": "gaussian",
            "ksize": ksize
        })

    candidates.append({
        "이름": (
            f"Bilateral (d={bilateral_d}, "
            f"color={bilateral_sigma_color}, "
            f"space={bilateral_sigma_space})"
        ),
        "filter": "bilateral",
        "d": bilateral_d,
        "sigma_color": bilateral_sigma_color,
        "sigma_space": bilateral_sigma_space
    })

    return candidates


def apply_candidate(img, candidate):
    if candidate["filter"] == "median":
        return cv2.medianBlur(img, candidate["ksize"])

    if candidate["filter"] == "gaussian":
        ksize = candidate["ksize"]
        return cv2.GaussianBlur(img, (ksize, ksize), 0)

    if candidate["filter"] == "bilateral":
        return cv2.bilateralFilter(
            img,
            candidate["d"],
            candidate["sigma_color"],
            candidate["sigma_space"]
        )

    raise ValueError("지원하지 않는 필터입니다.")


def calculate_score(
    before,
    after,
    flat_roi,
    lesion_roi,
    background_roi
):
    metrics = compare_quality(
        before,
        after,
        flat_roi,
        lesion_roi,
        background_roi
    )

    noise_reduction = metrics["noise_reduction"]
    edge_preservation = metrics["edge_preservation"]

    noise_score = max(0, min(noise_reduction, 1))
    edge_score = max(0, 1 - abs(edge_preservation - 1))

    score = noise_score * 50 + edge_score * 50

    return {
        "잡음 감소율": round(noise_reduction, 4),
        "경계 보존율": round(edge_preservation, 4),
        "처리 전 잡음": round(metrics["noise_before"], 2),
        "처리 후 잡음": round(metrics["noise_after"], 2),
        "처리 전 경계 대비": round(metrics["contrast_before"], 2),
        "처리 후 경계 대비": round(metrics["contrast_after"], 2),
        "점수": round(score, 2)
    }


def recommend_settings(
    img,
    flat_roi,
    lesion_roi,
    background_roi,
    median_ksizes=(3, 5, 7),
    gaussian_ksizes=(3, 5, 7),
    bilateral_d=9,
    bilateral_sigma_color=75,
    bilateral_sigma_space=75
):
    if not isinstance(img, np.ndarray):
        raise ValueError("영상은 NumPy 배열이어야 합니다.")

    if img.ndim != 2 or img.dtype != np.uint8:
        raise ValueError("8비트 흑백(2차원 uint8) 영상만 지원합니다.")

    candidates = generate_candidates(
        median_ksizes,
        gaussian_ksizes,
        bilateral_d,
        bilateral_sigma_color,
        bilateral_sigma_space
    )

    results = []

    for candidate in candidates:
        processed = apply_candidate(img, candidate)

        metrics = calculate_score(
            img,
            processed,
            flat_roi,
            lesion_roi,
            background_roi
        )

        results.append({
            "설정": candidate["이름"],
            **metrics
        })

    results.sort(
        key=lambda item: item["점수"],
        reverse=True
    )

    return results
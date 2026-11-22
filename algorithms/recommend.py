import cv2
import numpy as np

from algorithms.quality import brightness, contrast, sharpness


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


def calculate_score(img):
    b = brightness(img)
    c = contrast(img)
    s = sharpness(img)

    score = (
        min(b / 128, 1) * 20
        + min(c / 64, 1) * 30
        + min(s / 500, 1) * 50
    )

    return {
        "밝기": round(b, 2),
        "대비": round(c, 2),
        "선명도": round(s, 2),
        "점수": round(score, 2)
    }


def recommend_settings(
    img,
    median_ksizes=(3, 5, 7),
    gaussian_ksizes=(3, 5, 7),
    bilateral_d=9,
    bilateral_sigma_color=75,
    bilateral_sigma_space=75
):
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
        metrics = calculate_score(processed)

        results.append({
            "설정": candidate["이름"],
            "밝기": metrics["밝기"],
            "대비": metrics["대비"],
            "선명도": metrics["선명도"],
            "점수": metrics["점수"]
        })

    results.sort(
        key=lambda item: item["점수"],
        reverse=True
    )

    return results
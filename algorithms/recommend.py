import cv2
import numpy as np

from algorithms.quality import brightness, contrast, sharpness


def generate_candidates():
    return [
        {
            "이름": "Median 약하게",
            "filter": "median",
            "ksize": 3
        },
        {
            "이름": "Median 강하게",
            "filter": "median",
            "ksize": 5
        },
        {
            "이름": "Gaussian 약하게",
            "filter": "gaussian",
            "ksize": 3
        },
        {
            "이름": "Gaussian 강하게",
            "filter": "gaussian",
            "ksize": 5
        },
        {
            "이름": "Bilateral",
            "filter": "bilateral",
            "ksize": 5
        }
    ]


def apply_candidate(img, candidate):
    if candidate["filter"] == "median":
        return cv2.medianBlur(img, candidate["ksize"])

    if candidate["filter"] == "gaussian":
        return cv2.GaussianBlur(
            img,
            (candidate["ksize"], candidate["ksize"]),
            0
        )

    if candidate["filter"] == "bilateral":
        return cv2.bilateralFilter(img, 9, 75, 75)

    return img.copy()


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


def recommend_settings(img):
    candidates = generate_candidates()
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
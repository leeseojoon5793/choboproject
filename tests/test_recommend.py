import numpy as np
import pytest

from algorithms.recommend import (
    generate_candidates,
    calculate_score,
    recommend_settings
)


def test_generate_candidates():
    candidates = generate_candidates(
        median_ksizes=(3, 5),
        gaussian_ksizes=(3,),
    )

    assert len(candidates) == 4

    filters = [candidate["filter"] for candidate in candidates]

    assert filters.count("median") == 2
    assert filters.count("gaussian") == 1
    assert filters.count("bilateral") == 1


def test_generate_candidates_rejects_invalid_ksize():
    with pytest.raises(ValueError):
        generate_candidates(median_ksizes=(2,))


def test_calculate_score_uses_quality_metrics():
    before = np.tile(
        np.array([0, 50, 100, 150, 200], dtype=np.uint8),
        (20, 20)
    )

    after = before.copy()

    flat_roi = {"x": 0, "y": 0, "w": 5, "h": 20}
    lesion_roi = {"x": 0, "y": 0, "w": 3, "h": 20}
    background_roi = {"x": 2, "y": 0, "w": 3, "h": 20}
    result = calculate_score(
        before,
        after,
        flat_roi,
        lesion_roi,
        background_roi
    )

    assert result["잡음 감소율"] == 0
    assert result["경계 보존율"] == 1
    assert result["점수"] == 50


def test_recommend_settings_returns_ranked_results():
    rng = np.random.default_rng(42)

    img = rng.integers(
        0,
        256,
        size=(100, 100),
        dtype=np.uint8
    )

    flat_roi = {"x": 0, "y": 0, "w": 20, "h": 20}
    lesion_roi = {"x": 30, "y": 30, "w": 20, "h": 20}
    background_roi = {"x": 60, "y": 60, "w": 20, "h": 20}

    results = recommend_settings(
        img,
        flat_roi,
        lesion_roi,
        background_roi,
        median_ksizes=(3,),
        gaussian_ksizes=(3,)
    )

    assert len(results) == 3

    scores = [result["점수"] for result in results]

    assert scores == sorted(scores, reverse=True)

    assert "잡음 감소율" in results[0]
    assert "경계 보존율" in results[0]


def test_recommend_settings_rejects_invalid_image():
    img = np.zeros((20, 20, 3), dtype=np.uint8)

    roi = {"x": 0, "y": 0, "w": 5, "h": 5}

    with pytest.raises(ValueError):
        recommend_settings(
            img,
            roi,
            roi,
            roi
        )
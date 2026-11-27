from datetime import datetime, timezone

import numpy as np
import pytest
from PIL import Image

from modules.result_image import make_result_path, save_result_image


def test_result_path_format():
    now = datetime(2026, 11, 27, 11, 30, 5, tzinfo=timezone.utc)
    path = make_result_path("C001", "C001_003", "median", now=now)
    assert path == "results/C001/C001_003_median_20261127T113005Z.png"


def test_saved_image_has_same_pixels(tmp_path, monkeypatch):
    monkeypatch.setattr("modules.paths.get_data_dir", lambda: tmp_path)
    img = np.arange(16, dtype=np.uint8).reshape(4, 4)

    save_result_image(img, "results/C001/a.png")

    saved = np.array(Image.open(tmp_path / "results/C001/a.png"))
    assert np.array_equal(saved, img)


def test_bad_path_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr("modules.paths.get_data_dir", lambda: tmp_path)
    with pytest.raises(ValueError):
        save_result_image(np.zeros((2, 2), np.uint8), "../outside.png")

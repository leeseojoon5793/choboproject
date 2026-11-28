from datetime import datetime, timezone

import numpy as np
import pytest
from PIL import Image

from modules.result_image import make_result_path, save_processed_result, save_result_image


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


CASE = {"case_id": "C001", "created_by": "reg-1", "assignee": "rev-1", "status": "in_review"}


def save_args(tmp_path, **kwargs):
    args = dict(
        role="reviewer", uid="rev-1", case=CASE, image_id="C001_001",
        algorithm="median", algorithm_version="1.0", params={"ksize": 3},
        roi={"x": 0, "y": 0, "w": 2, "h": 2}, img=np.zeros((4, 4), np.uint8),
        metrics={"after": {"std": 1.0}}, local_db_path=tmp_path / "logs.json",
    )
    args.update(kwargs)
    return args


def saved_pngs(tmp_path):
    return list(tmp_path.rglob("*.png"))


def test_save_processed_result_keeps_image_and_log(tmp_path, monkeypatch):
    monkeypatch.setattr("modules.paths.get_data_dir", lambda: tmp_path)

    log = save_processed_result(**save_args(tmp_path))

    assert (tmp_path / log["result_path"]).exists()
    assert (tmp_path / "logs.json").exists()


def test_no_permission_leaves_no_image(tmp_path, monkeypatch):
    monkeypatch.setattr("modules.paths.get_data_dir", lambda: tmp_path)

    with pytest.raises(PermissionError):
        save_processed_result(**save_args(tmp_path, uid="rev-2"))  # 담당이 아닌 reviewer

    assert saved_pngs(tmp_path) == []


class BrokenFirestore:
    """저장할 때 네트워크 오류 같은 예외를 내는 가짜 Firestore."""

    def collection(self, name):
        return self

    def document(self, doc_id):
        return self

    def set(self, value):
        raise RuntimeError("연결 실패")


def test_other_error_also_removes_image(tmp_path, monkeypatch):
    monkeypatch.setattr("modules.paths.get_data_dir", lambda: tmp_path)

    with pytest.raises(RuntimeError):
        save_processed_result(**save_args(tmp_path, firestore_client=BrokenFirestore()))

    assert saved_pngs(tmp_path) == []

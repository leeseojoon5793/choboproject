import json
import re

import pytest

from modules.process_log import list_process_logs, save_process_log

CASE = {"case_id": "C001", "created_by": "reg-1", "assignee": "rev-1", "status": "in_review"}


def save(tmp_path, role="reviewer", uid="rev-1", image_id="C001_000", **kwargs):
    args = dict(
        role=role,
        uid=uid,
        case=CASE,
        image_id=image_id,
        algorithm="median",
        algorithm_version="1.0",
        params={"ksize": 3},
        roi={"x": 10, "y": 20, "w": 30, "h": 40},
        result_path="results/C001/C001_000_median.png",
        metrics={"mean": 120.5, "std": 8.2},
        local_db_path=tmp_path / "logs.json",
    )
    args.update(kwargs)
    return save_process_log(**args)


class FakeDoc:
    def __init__(self, doc_id, data):
        self.id = doc_id
        self._data = data

    def to_dict(self):
        return dict(self._data)


class FakeFirestore:
    """collection(...).document(...).set(...)과 collection(...).stream()만 흉내 낸다."""

    def __init__(self):
        self.data = {}
        self._collection = None
        self._doc_id = None

    def collection(self, name):
        self._collection = name
        return self

    def document(self, doc_id):
        self._doc_id = doc_id
        return self

    def set(self, value):
        self.data.setdefault(self._collection, {})[self._doc_id] = value

    def stream(self):
        return [FakeDoc(k, v) for k, v in self.data.get(self._collection, {}).items()]


def test_saved_log_has_all_fields(tmp_path):
    log = save(tmp_path)
    assert log["case_id"] == "C001"
    assert log["image_id"] == "C001_000"
    assert log["algorithm"] == "median"
    assert log["algorithm_version"] == "1.0"
    assert log["params"] == {"ksize": 3}
    assert log["roi"] == {"x": 10, "y": 20, "w": 30, "h": 40}
    assert log["result_path"] == "results/C001/C001_000_median.png"
    assert log["metrics"] == {"mean": 120.5, "std": 8.2}
    assert log["run_by"] == "rev-1"
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", log["created_at"])


def test_save_then_list(tmp_path):
    saved = save(tmp_path)
    logs = list_process_logs("C001_000", local_db_path=tmp_path / "logs.json")
    assert logs == [saved]


def test_roi_can_be_none(tmp_path):
    assert save(tmp_path, roi=None)["roi"] is None


@pytest.mark.parametrize(
    "role, uid",
    [
        ("reviewer", "rev-1"),  # 담당 reviewer
        ("register", "reg-1"),  # 케이스 만든 사람
        ("admin", "anyone"),
    ],
)
def test_allowed_users_can_save(tmp_path, role, uid):
    assert save(tmp_path, role=role, uid=uid)["run_by"] == uid


@pytest.mark.parametrize(
    "role, uid",
    [
        ("reviewer", "rev-2"),  # 담당이 아닌 reviewer
        ("register", "reg-2"),  # 다른 사람 케이스
    ],
)
def test_no_permission_saves_nothing(tmp_path, role, uid):
    with pytest.raises(PermissionError):
        save(tmp_path, role=role, uid=uid)
    assert not (tmp_path / "logs.json").exists()


def test_absolute_result_path_rejected(tmp_path):
    with pytest.raises(ValueError, match="상대 경로"):
        save(tmp_path, result_path="/home/server/data/results/a.png")


def test_list_filters_by_image_and_sorts_newest_first(tmp_path):
    db_path = tmp_path / "logs.json"
    records = {
        "a": {"image_id": "C001_000", "created_at": "2026-11-24T01:00:00Z"},
        "b": {"image_id": "C001_001", "created_at": "2026-11-24T02:00:00Z"},
        "c": {"image_id": "C001_000", "created_at": "2026-11-24T03:00:00Z"},
    }
    db_path.write_text(json.dumps(records), encoding="utf-8")

    logs = list_process_logs("C001_000", local_db_path=db_path)
    assert [log["log_id"] for log in logs] == ["c", "a"]


def test_list_without_file_is_empty(tmp_path):
    assert list_process_logs("C001_000", local_db_path=tmp_path / "none.json") == []


def test_firestore_save_and_list(tmp_path):
    db = FakeFirestore()
    saved = save(tmp_path, firestore_client=db)

    assert list(db.data) == ["process_logs"]
    assert not (tmp_path / "logs.json").exists()
    assert list_process_logs("C001_000", firestore_client=db) == [saved]

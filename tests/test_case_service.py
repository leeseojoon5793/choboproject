import json

import pytest

from modules.case_service import change_status, list_visible_cases
from modules.paths import data_path


def seed(tmp_path, **case):
    base = {"case_id": "C001", "status": "received", "created_by": "u-reg", "assignee": "",
            "created_at": "2026-11-23T00:00:00Z"}
    base.update(case)
    (tmp_path / "cases_local.json").write_text(json.dumps({base["case_id"]: base}), encoding="utf-8")


def read(tmp_path, name):
    return json.loads((tmp_path / name).read_text(encoding="utf-8"))


def test_admin_assigns_and_log_written(tmp_path):
    seed(tmp_path)
    ok, _ = change_status(None, "admin", "u-admin", "C001", "assigned", assignee="u-rev", data_dir=tmp_path)
    assert ok
    case = read(tmp_path, "cases_local.json")["C001"]
    assert case["status"] == "assigned" and case["assignee"] == "u-rev"
    log = list(read(tmp_path, "status_logs_local.json").values())[0]
    assert (log["from_status"], log["to_status"], log["changed_by"]) == ("received", "assigned", "u-admin")


def test_assign_without_assignee_rejected(tmp_path):
    seed(tmp_path)
    ok, msg = change_status(None, "admin", "u-admin", "C001", "assigned", data_dir=tmp_path)
    assert not ok and "검토 담당" in msg


def test_recheck_requires_reason_and_saves_it(tmp_path):
    seed(tmp_path, status="in_review", assignee="u-rev")
    assert not change_status(None, "reviewer", "u-rev", "C001", "recheck", data_dir=tmp_path)[0]
    ok, _ = change_status(None, "reviewer", "u-rev", "C001", "recheck", reason="노이즈 심함", data_dir=tmp_path)
    assert ok
    log = list(read(tmp_path, "status_logs_local.json").values())[0]
    assert log["reason"] == "노이즈 심함"


def test_rejected_change_leaves_no_trace(tmp_path):
    seed(tmp_path, status="in_review", assignee="u-rev")
    ok, _ = change_status(None, "reviewer", "u-other", "C001", "done", data_dir=tmp_path)
    assert not ok
    assert read(tmp_path, "cases_local.json")["C001"]["status"] == "in_review"
    assert not (tmp_path / "status_logs_local.json").exists()


def test_missing_case(tmp_path):
    seed(tmp_path)
    ok, msg = change_status(None, "admin", "u-admin", "C999", "assigned", assignee="u", data_dir=tmp_path)
    assert not ok and "C999" in msg


def test_register_sees_only_own_cases(tmp_path):
    cases = {
        "C001": {"case_id": "C001", "title": "a", "status": "received", "created_by": "u-reg", "assignee": "", "created_at": "1"},
        "C002": {"case_id": "C002", "title": "b", "status": "received", "created_by": "u-x", "assignee": "", "created_at": "2"},
    }
    db_path = tmp_path / "cases_local.json"
    db_path.write_text(json.dumps(cases), encoding="utf-8")
    mine = list_visible_cases(None, "register", "u-reg", local_db_path=db_path)
    assert [c["case_id"] for c in mine] == ["C001"]
    assert len(list_visible_cases(None, "reviewer", "u-rev", local_db_path=db_path)) == 2


def test_data_path_rejects_unsafe_paths():
    assert data_path("low_dose_images/C001/001.png").parts[-3:] == ("low_dose_images", "C001", "001.png")
    with pytest.raises(ValueError):
        data_path("../secrets.toml")
    with pytest.raises(ValueError):
        data_path("/etc/passwd")
import pytest

from modules.memo import add_memo, list_memos

CASE = {"case_id": "C001", "status": "in_review", "created_by": "u-reg", "assignee": "u-rev"}


def test_add_and_list(tmp_path):
    db = tmp_path / "memos.json"
    saved = add_memo("reviewer", "u-rev", CASE, "  폐야 경계 확인  ", memo_type="report", local_db_path=db)
    assert saved["content"] == "폐야 경계 확인" and saved["type"] == "report"
    memos = list_memos("C001", local_db_path=db)
    assert [m["memo_id"] for m in memos] == [saved["memo_id"]]
    assert list_memos("C999", local_db_path=db) == []


def test_empty_or_too_long_rejected(tmp_path):
    db = tmp_path / "memos.json"
    with pytest.raises(ValueError):
        add_memo("reviewer", "u-rev", CASE, "   ", local_db_path=db)
    with pytest.raises(ValueError):
        add_memo("reviewer", "u-rev", CASE, "가" * 1001, local_db_path=db)
    with pytest.raises(ValueError):
        add_memo("reviewer", "u-rev", CASE, "내용", memo_type="note", local_db_path=db)
    assert not db.exists()


def test_permission(tmp_path):
    db = tmp_path / "memos.json"
    with pytest.raises(PermissionError):
        add_memo("reviewer", "u-other", CASE, "내용", local_db_path=db)
    with pytest.raises(PermissionError):
        add_memo("register", "u-reg", CASE, "소견", memo_type="report", local_db_path=db)
    add_memo("register", "u-reg", CASE, "재촬영 예정", local_db_path=db)
    add_memo("admin", "u-admin", CASE, "확인함", memo_type="report", local_db_path=db)
    assert len(list_memos("C001", local_db_path=db)) == 2


def test_newest_first(tmp_path, monkeypatch):
    db = tmp_path / "memos.json"
    times = iter(["2026-11-24T00:00:00Z", "2026-11-24T00:00:05Z"])
    monkeypatch.setattr("modules.memo._now_utc_z", lambda: next(times))
    first = add_memo("reviewer", "u-rev", CASE, "첫 번째", local_db_path=db)
    second = add_memo("reviewer", "u-rev", CASE, "두 번째", local_db_path=db)
    assert [m["memo_id"] for m in list_memos("C001", local_db_path=db)] == [second["memo_id"], first["memo_id"]]
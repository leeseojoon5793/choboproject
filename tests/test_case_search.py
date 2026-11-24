import json
import cv2
import numpy as np
from modules.case_repository import register_case, search_cases


def _make_png_bytes() -> bytes:
    img = np.full((64, 64), 120, dtype=np.uint8)
    ok, encoded = cv2.imencode(".png", img)
    assert ok
    return encoded.tobytes()


def _seed_cases(tmp_path):
    img_dir = tmp_path / "low_dose_images"
    db_path = tmp_path / "cases_local.json"
    images_db = tmp_path / "images_local.json"
    png_bytes = _make_png_bytes()

    register_case(
        case_id="C001",
        title="Siemens Chest Low Dose",
        created_by="register-user-1",
        file_name="001.png",
        file_bytes=png_bytes,
        assignee="",
        image_dir=img_dir,
        local_db_path=db_path,
        local_images_db_path=images_db,
        data_dir=tmp_path,
    )
    register_case(
        case_id="C002",
        title="GE Lung Screening",
        created_by="register-user-2",
        file_name="002.png",
        file_bytes=png_bytes,
        assignee="reviewer-user-1",
        image_dir=img_dir,
        local_db_path=db_path,
        local_images_db_path=images_db,
        data_dir=tmp_path,
    )
    data = json.loads(db_path.read_text(encoding="utf-8"))
    data["C002"]["status"] = "assigned"
    data["C002"]["body_part"] = "ABDOMEN"
    db_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return db_path


def test_search_cases_by_keyword(tmp_path):
    db_path = _seed_cases(tmp_path)

    res_id = search_cases(keyword="c001", local_db_path=db_path)
    assert len(res_id) == 1
    assert res_id[0]["case_id"] == "C001"

    res_title = search_cases(keyword="lung", local_db_path=db_path)
    assert len(res_title) == 1
    assert res_title[0]["case_id"] == "C002"


def test_filter_cases_by_status_and_assignee(tmp_path):
    db_path = _seed_cases(tmp_path)

    received = search_cases(status="received", local_db_path=db_path)
    assert [c["case_id"] for c in received] == ["C001"]

    assigned = search_cases(status="assigned", assignee="reviewer-user-1", local_db_path=db_path)
    assert [c["case_id"] for c in assigned] == ["C002"]


def test_filter_cases_by_body_part_and_combined(tmp_path):
    db_path = _seed_cases(tmp_path)

    chest = search_cases(body_part="chest", created_by="register-user-1", local_db_path=db_path)
    assert [c["case_id"] for c in chest] == ["C001"]

    empty = search_cases(keyword="Siemens", status="done", local_db_path=db_path)
    assert empty == []


def test_filter_cases_unassigned_only(tmp_path):
    db_path = _seed_cases(tmp_path)

    unassigned = search_cases(unassigned_only=True, local_db_path=db_path)
    assert [c["case_id"] for c in unassigned] == ["C001"]

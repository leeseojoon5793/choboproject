import cv2
import numpy as np
import pytest
from modules.case_repository import register_case


def _make_png_bytes() -> bytes:
    img = np.zeros((64, 64), dtype=np.uint8)
    ok, encoded = cv2.imencode(".png", img)
    assert ok
    return encoded.tobytes()


def test_register_case_saves_image_and_metadata(tmp_path):
    img_dir = tmp_path / "low_dose_images"
    db_path = tmp_path / "cases_local.json"
    png_bytes = _make_png_bytes()

    result = register_case(
        case_id="CT-CHEST-001",
        title="흉부 저선량 CT #01",
        file_name="slice_001.png",
        file_bytes=png_bytes,
        created_by="fake-register",
        assignee="fake-reviewer",
        image_dir=img_dir,
        local_db_path=db_path,
    )

    assert result["case_id"] == "CT-CHEST-001"
    assert result["status"] == "received"
    assert result["created_by"] == "fake-register"
    assert result["assignee"] == "fake-reviewer"
    assert (img_dir / "CT-CHEST-001.png").exists()
    assert db_path.exists()


def test_register_case_prevents_duplicate_id(tmp_path):
    img_dir = tmp_path / "low_dose_images"
    db_path = tmp_path / "cases_local.json"
    png_bytes = _make_png_bytes()

    register_case(
        case_id="CT-CHEST-001",
        title="첫 번째 등록",
        file_name="slice_001.png",
        file_bytes=png_bytes,
        created_by="fake-register",
        image_dir=img_dir,
        local_db_path=db_path,
    )

    with pytest.raises(ValueError, match="이미 등록된"):
        register_case(
            case_id="CT-CHEST-001",
            title="중복 등록 시도",
            file_name="slice_001.png",
            file_bytes=png_bytes,
            created_by="fake-register",
            image_dir=img_dir,
            local_db_path=db_path,
        )

from pathlib import Path
import cv2
import numpy as np
import pytest
from modules.case_repository import register_case, register_slice
from modules.case_validator import CaseValidationError


def _make_png_bytes(width: int = 128, height: int = 128) -> bytes:
    img = np.full((height, width), 100, dtype=np.uint8)
    ok, encoded = cv2.imencode(".png", img)
    assert ok
    return encoded.tobytes()


def test_register_case_and_slice_metadata(tmp_path):
    img_dir = tmp_path / "low_dose_images"
    cases_db = tmp_path / "cases_local.json"
    images_db = tmp_path / "images_local.json"
    png_bytes = _make_png_bytes()

    result = register_case(
        case_id="CT-CHEST-001",
        title="흉부 저선량 CT #01",
        created_by="register-user-1",
        file_name="slice_001.png",
        file_bytes=png_bytes,
        assignee="reviewer-user-1",
        image_dir=img_dir,
        local_db_path=cases_db,
        local_images_db_path=images_db,
        data_dir=tmp_path,
    )

    assert result["case_id"] == "CT-CHEST-001"
    assert result["status"] == "received"
    assert result["created_at"].endswith("Z")
    # DB에는 data_dir 기준 상대 경로만 저장되어야 함
    assert result["storage_paths"]["low_dose_dir"] == "low_dose_images/CT-CHEST-001"
    assert (img_dir / "CT-CHEST-001" / "001.png").exists()

    # 추가 슬라이스 등록 확인 (z_position 미전달 시 None)
    slice_2 = register_slice(
        case_id="CT-CHEST-001",
        slice_index=2,
        file_name="slice_002.png",
        file_bytes=png_bytes,
        uploaded_by="register-user-1",
        image_dir=img_dir,
        local_images_db_path=images_db,
        data_dir=tmp_path,
    )
    assert slice_2["image_id"] == "CT-CHEST-001_002"
    assert slice_2["file_path"] == "low_dose_images/CT-CHEST-001/002.png"
    assert slice_2["z_position"] is None

    # 같은 slice_index 중복 등록 시 에러 발생 확인
    with pytest.raises(CaseValidationError, match="이미 등록된 슬라이스"):
        register_slice(
            case_id="CT-CHEST-001",
            slice_index=2,
            file_name="slice_002_dup.png",
            file_bytes=png_bytes,
            uploaded_by="register-user-1",
            image_dir=img_dir,
            local_images_db_path=images_db,
            data_dir=tmp_path,
        )


def test_register_case_rejects_duplicate_id(tmp_path):
    img_dir = tmp_path / "low_dose_images"
    cases_db = tmp_path / "cases_local.json"
    images_db = tmp_path / "images_local.json"
    png_bytes = _make_png_bytes()

    register_case(
        case_id="DUP-001",
        title="첫 번째 케이스",
        created_by="register-user-1",
        file_name="001.png",
        file_bytes=png_bytes,
        image_dir=img_dir,
        local_db_path=cases_db,
        local_images_db_path=images_db,
        data_dir=tmp_path,
    )

    with pytest.raises(CaseValidationError):
        register_case(
            case_id="DUP-001",
            title="중복 케이스",
            created_by="register-user-1",
            file_name="002.png",
            file_bytes=png_bytes,
            image_dir=img_dir,
            local_db_path=cases_db,
            local_images_db_path=images_db,
            data_dir=tmp_path,
        )


def test_register_case_default_metadata_values(tmp_path):
    img_dir = tmp_path / "low_dose_images"
    cases_db = tmp_path / "cases_local.json"
    images_db = tmp_path / "images_local.json"
    png_bytes = _make_png_bytes()

    result = register_case(
        case_id="DEFAULT-META-001",
        title="기본 메타데이터 테스트",
        created_by="register-user-1",
        file_name="001.png",
        file_bytes=png_bytes,
        image_dir=img_dir,
        local_db_path=cases_db,
        local_images_db_path=images_db,
        data_dir=tmp_path,
    )

    assert result["manufacturer"] == "SIEMENS"
    assert result["model"] == "Somatom Definition Flash"
    assert result["slice_thickness_mm"] == 1.5

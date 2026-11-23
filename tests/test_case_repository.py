import io
from pathlib import Path
from PIL import Image
from modules.case_repository import register_case, register_slice
from modules.case_validator import CaseValidationError


def _make_png_bytes(width: int = 128, height: int = 128) -> bytes:
    img = Image.new("L", (width, height), color=100)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_register_case_and_slice_metadata(tmp_path):
    img_dir = tmp_path / "low_dose_images"
    cases_db = tmp_path / "cases_local.json"
    images_db = tmp_path / "images_local.json"
    png_bytes = _make_png_bytes()

    result = register_case(
        case_id="CT-CHEST-001",
        title="흉부 저선량 CT #01",
        file_name="slice_001.png",
        file_bytes=png_bytes,
        created_by="fake-register",
        assignee="fake-reviewer",
        image_dir=img_dir,
        local_db_path=cases_db,
        local_images_db_path=images_db,
    )

    assert result["case_id"] == "CT-CHEST-001"
    assert result["status"] == "received"
    assert result["created_at"].endswith("Z")
    assert result["storage_paths"]["low_dose_dir"] == str(img_dir / "CT-CHEST-001")
    assert (img_dir / "CT-CHEST-001" / "001.png").exists()

    # 추가 슬라이스 등록 확인
    slice_2 = register_slice(
        case_id="CT-CHEST-001",
        slice_index=2,
        file_name="slice_002.png",
        file_bytes=png_bytes,
        uploaded_by="fake-register",
        z_position=-320.5,
        image_dir=img_dir,
        local_images_db_path=images_db,
    )
    assert slice_2["image_id"] == "CT-CHEST-001_002"
    assert slice_2["z_position"] == -320.5
    assert Path(slice_2["file_path"]).exists()


def test_register_case_rejects_duplicate_id(tmp_path):
    img_dir = tmp_path / "low_dose_images"
    cases_db = tmp_path / "cases_local.json"
    images_db = tmp_path / "images_local.json"
    png_bytes = _make_png_bytes()

    register_case(
        case_id="DUP-001",
        title="첫 번째 케이스",
        file_name="001.png",
        file_bytes=png_bytes,
        image_dir=img_dir,
        local_db_path=cases_db,
        local_images_db_path=images_db,
    )

    try:
        register_case(
            case_id="DUP-001",
            title="중복 케이스",
            file_name="002.png",
            file_bytes=png_bytes,
            image_dir=img_dir,
            local_db_path=cases_db,
            local_images_db_path=images_db,
        )
        assert False, "중복 ID에서 CaseValidationError가 발생해야 합니다."
    except CaseValidationError:
        pass

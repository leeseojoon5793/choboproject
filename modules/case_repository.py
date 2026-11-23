import json
from datetime import datetime, timezone
from pathlib import Path
from modules.case_validator import (
    CaseValidationError,
    validate_case_id,
    validate_image_file,
)

DEFAULT_DATA_DIR = Path("data")
LOCAL_DB_PATH = DEFAULT_DATA_DIR / "cases_local.json"
LOCAL_IMAGES_DB_PATH = DEFAULT_DATA_DIR / "images_local.json"
DEFAULT_IMAGE_DIR = DEFAULT_DATA_DIR / "low_dose_images"


def get_base_data_dir() -> Path:
    """secrets.toml의 data_dir 설정이 있으면 반환하고, 없으면 기본 data/ 경로를 반환한다."""
    try:
        import streamlit as st
        configured = st.secrets.get("data_dir")
        if configured:
            return Path(str(configured))
    except Exception:
        pass
    return DEFAULT_DATA_DIR


def _now_utc_z() -> str:
    """팀 규칙에 맞춘 UTC ISO 8601 Z 포맷 시각 문자열을 반환한다."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_json_dict(db_path: Path) -> dict:
    if not db_path.exists():
        return {}
    try:
        return json.loads(db_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _save_json_dict(records: dict, db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db_path.write_text(
        json.dumps(records, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def register_slice(
    case_id: str,
    slice_index: int,
    file_name: str,
    file_bytes: bytes,
    uploaded_by: str = "fake-register",
    z_position: float | None = None,
    image_dir: Path | None = None,
    firestore_client=None,
    local_images_db_path: Path | None = None,
) -> dict:
    """단일 슬라이스 영상을 디스크에 저장하고 images 컬렉션(또는 로컬 JSON)에 메타데이터를 기록한다.
    DB 저장 중 예외가 발생하면 방금 저장한 이미지 파일을 즉시 삭제해 정합성을 유지한다.
    """
    img_info = validate_image_file(file_name, file_bytes)

    base_dir = get_base_data_dir()
    target_root = Path(image_dir) if image_dir is not None else (base_dir / "low_dose_images")
    images_db_path = (
        Path(local_images_db_path)
        if local_images_db_path is not None
        else (base_dir / "images_local.json")
    )

    image_id = f"{case_id}_{slice_index:03d}"
    case_folder = target_root / case_id
    case_folder.mkdir(parents=True, exist_ok=True)

    saved_file_name = f"{slice_index:03d}{img_info['extension']}"
    saved_path = case_folder / saved_file_name
    saved_path.write_bytes(file_bytes)

    now_z = _now_utc_z()
    image_doc = {
        "image_id": image_id,
        "case_id": case_id,
        "slice_index": slice_index,
        "z_position": float(z_position) if z_position is not None else float(slice_index),
        "file_path": str(saved_path),
        "width": img_info["width"],
        "height": img_info["height"],
        "size_bytes": img_info["size_bytes"],
        "uploaded_by": uploaded_by,
        "uploaded_at": now_z,
    }

    try:
        if firestore_client is not None:
            firestore_client.collection("images").document(image_id).set(image_doc)
        else:
            local_images = _load_json_dict(images_db_path)
            local_images[image_id] = image_doc
            _save_json_dict(local_images, images_db_path)
    except Exception:
        saved_path.unlink(missing_ok=True)
        raise

    return image_doc


def register_case(
    case_id: str,
    title: str,
    file_name: str | None = None,
    file_bytes: bytes | None = None,
    created_by: str = "fake-register",
    assignee: str = "",
    manufacturer: str = "SIEMENS",
    model: str = "",
    body_part: str = "CHEST",
    slice_thickness_mm: float = 1.5,
    total_slices: int = 1,
    window_setting: dict | None = None,
    image_dir: Path | None = None,
    firestore_client=None,
    local_db_path: Path | None = None,
    local_images_db_path: Path | None = None,
) -> dict:
    """신규 케이스 메타데이터를 cases 컬렉션에 저장하고, 초기 파일이 전달되면 첫 슬라이스(images)도 함께 등록한다.
    DB 저장 중 예외가 발생하면 저장된 파일도 함께 롤백한다.
    """
    if not isinstance(title, str) or not title.strip():
        raise CaseValidationError("케이스 제목을 입력해 주세요.")

    base_dir = get_base_data_dir()
    db_path = Path(local_db_path) if local_db_path is not None else (base_dir / "cases_local.json")
    target_root = Path(image_dir) if image_dir is not None else (base_dir / "low_dose_images")

    local_cases = {} if firestore_client is not None else _load_json_dict(db_path)
    cleaned_id = validate_case_id(
        case_id,
        existing_ids=None if firestore_client is not None else set(local_cases.keys()),
        firestore_client=firestore_client,
    )

    low_dose_dir = str(target_root / cleaned_id)
    now_z = _now_utc_z()

    case_data = {
        "case_id": cleaned_id,
        "title": title.strip(),
        "manufacturer": manufacturer,
        "model": model,
        "body_part": body_part,
        "slice_thickness_mm": float(slice_thickness_mm),
        "total_slices": int(total_slices),
        "window_setting": window_setting or {"center": -600, "width": 1500},
        "storage_paths": {
            "low_dose_dir": low_dose_dir,
        },
        "status": "received",
        "created_by": created_by,
        "assignee": assignee,
        "created_at": now_z,
        "updated_at": now_z,
    }

    first_slice = None
    if file_name is not None and file_bytes is not None:
        first_slice = register_slice(
            case_id=cleaned_id,
            slice_index=1,
            file_name=file_name,
            file_bytes=file_bytes,
            uploaded_by=created_by,
            image_dir=target_root,
            firestore_client=firestore_client,
            local_images_db_path=local_images_db_path,
        )

    try:
        if firestore_client is not None:
            firestore_client.collection("cases").document(cleaned_id).set(case_data)
        else:
            local_cases[cleaned_id] = case_data
            _save_json_dict(local_cases, db_path)
    except Exception:
        if first_slice is not None:
            Path(first_slice["file_path"]).unlink(missing_ok=True)
        raise

    return case_data

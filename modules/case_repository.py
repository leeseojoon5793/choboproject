from datetime import datetime, timezone
import json
from pathlib import Path
from modules.case_validator import validate_case_id, validate_image_file

IMAGE_DIR = Path("data/low_dose_images")
LOCAL_DB_PATH = Path("data/cases_local.json")


def _load_local_cases(db_path: Path = LOCAL_DB_PATH) -> dict:
    if not db_path.exists():
        return {}
    return json.loads(db_path.read_text(encoding="utf-8"))


def _save_local_cases(cases: dict, db_path: Path = LOCAL_DB_PATH) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db_path.write_text(
        json.dumps(cases, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def register_case(
    case_id: str,
    title: str,
    file_name: str,
    file_bytes: bytes,
    created_by: str,
    assignee: str = "",
    window_center: int = -600,
    window_width: int = 1500,
    firestore_client=None,
    image_dir: Path = IMAGE_DIR,
    local_db_path: Path = LOCAL_DB_PATH,
) -> dict:
    """저선량 CT PNG 파일을 로컬 폴더에 저장하고 케이스 메타데이터를 등록한다."""
    img_info = validate_image_file(file_name, file_bytes)

    if firestore_client is not None:
        existing_docs = firestore_client.collection("cases").stream()
        existing_ids = {doc.id for doc in existing_docs}
    else:
        local_cases = _load_local_cases(local_db_path)
        existing_ids = set(local_cases.keys())

    cleaned_id = validate_case_id(case_id, existing_ids)

    image_dir.mkdir(parents=True, exist_ok=True)
    ext = Path(file_name).suffix.lower()
    saved_path = image_dir / f"{cleaned_id}{ext}"
    saved_path.write_bytes(file_bytes)

    case_data = {
        "case_id": cleaned_id,
        "title": title.strip() or cleaned_id,
        "modality": "CT",
        "body_part": "Chest",
        "dose_type": "low_dose",
        "window_center": int(window_center),
        "window_width": int(window_width),
        "image_path": str(saved_path),
        "width": img_info["width"],
        "height": img_info["height"],
        "status": "uploaded",
        "created_by": created_by,
        "assignee": assignee,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    if firestore_client is not None:
        firestore_client.collection("cases").document(cleaned_id).set(case_data)
    else:
        local_cases[cleaned_id] = case_data
        _save_local_cases(local_cases, local_db_path)

    return case_data

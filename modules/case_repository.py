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


def _to_db_relative_path(target_path: Path, base_dir: Path) -> str:
    """실행 환경(서버/로컬)에 무관하도록 data_dir 기준 상대 경로(POSIX 형식)를 반환한다."""
    try:
        return target_path.relative_to(base_dir).as_posix()
    except ValueError:
        return target_path.as_posix()


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
    uploaded_by: str,
    z_position: float | None = None,
    image_dir: Path | None = None,
    firestore_client=None,
    local_images_db_path: Path | None = None,
    data_dir: Path | None = None,
) -> dict:
    """단일 슬라이스 영상을 디스크에 저장하고 images 컬렉션에 data_dir 기준 상대 경로로 기록한다.
    중복 slice_index 호출 시 에러를 발생시키고, DB 저장 실패 시 방금 저장한 파일을 롤백한다.
    """
    if not isinstance(uploaded_by, str) or not uploaded_by.strip():
        raise CaseValidationError("업로드 사용자 ID(uploaded_by)를 입력해 주세요.")

    img_info = validate_image_file(file_name, file_bytes)

    base_dir = Path(data_dir) if data_dir is not None else get_base_data_dir()
    target_root = Path(image_dir) if image_dir is not None else (base_dir / "low_dose_images")
    images_db_path = (
        Path(local_images_db_path)
        if local_images_db_path is not None
        else (base_dir / "images_local.json")
    )

    image_id = f"{case_id}_{slice_index:03d}"
    case_folder = target_root / case_id
    saved_file_name = f"{slice_index:03d}{img_info['extension']}"
    saved_path = case_folder / saved_file_name

    # 중복 slice_index 덮어쓰기 방지
    if firestore_client is not None:
        existing_snap = firestore_client.collection("images").document(image_id).get()
        if getattr(existing_snap, "exists", False):
            raise CaseValidationError(f"이미 등록된 슬라이스입니다: {image_id}")
    else:
        local_images = _load_json_dict(images_db_path)
        if image_id in local_images or saved_path.exists():
            raise CaseValidationError(f"이미 등록된 슬라이스입니다: {image_id}")

    case_folder.mkdir(parents=True, exist_ok=True)
    saved_path.write_bytes(file_bytes)

    rel_file_path = _to_db_relative_path(saved_path, base_dir)
    now_z = _now_utc_z()
    image_doc = {
        "image_id": image_id,
        "case_id": case_id,
        "slice_index": slice_index,
        "z_position": float(z_position) if z_position is not None else None,
        "file_path": rel_file_path,
        "width": img_info["width"],
        "height": img_info["height"],
        "size_bytes": img_info["size_bytes"],
        "uploaded_by": uploaded_by.strip(),
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
    created_by: str,
    file_name: str | None = None,
    file_bytes: bytes | None = None,
    assignee: str = "",
    manufacturer: str = "SIEMENS",
    model: str = "Somatom Definition Flash",
    body_part: str = "CHEST",
    slice_thickness_mm: float = 1.5,
    total_slices: int = 1,
    window_setting: dict | None = None,
    image_dir: Path | None = None,
    firestore_client=None,
    local_db_path: Path | None = None,
    local_images_db_path: Path | None = None,
    data_dir: Path | None = None,
) -> dict:
    """cases 문서를 먼저 저장한 뒤 초기 슬라이스를 등록한다.
    슬라이스 등록 중 예외가 발생하면 방금 생성한 cases 문서를 즉시 삭제해 정합성을 유지한다.
    """
    if not isinstance(title, str) or not title.strip():
        raise CaseValidationError("케이스 제목을 입력해 주세요.")
    if not isinstance(created_by, str) or not created_by.strip():
        raise CaseValidationError("등록자 ID(created_by)를 입력해 주세요.")

    base_dir = Path(data_dir) if data_dir is not None else get_base_data_dir()
    db_path = Path(local_db_path) if local_db_path is not None else (base_dir / "cases_local.json")
    target_root = Path(image_dir) if image_dir is not None else (base_dir / "low_dose_images")

    local_cases = {} if firestore_client is not None else _load_json_dict(db_path)
    cleaned_id = validate_case_id(
        case_id,
        existing_ids=None if firestore_client is not None else set(local_cases.keys()),
        firestore_client=firestore_client,
    )

    rel_low_dose_dir = _to_db_relative_path(target_root / cleaned_id, base_dir)
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
            "low_dose_dir": rel_low_dose_dir,
        },
        "status": "received",
        "created_by": created_by.strip(),
        "assignee": assignee,
        "created_at": now_z,
        "updated_at": now_z,
    }

    # 1단계: cases 문서 먼저 저장
    if firestore_client is not None:
        firestore_client.collection("cases").document(cleaned_id).set(case_data)
    else:
        local_cases[cleaned_id] = case_data
        _save_json_dict(local_cases, db_path)

    # 2단계: 초기 슬라이스 등록 (실패 시 방금 저장한 cases 문서 롤백 삭제)
    if file_name is not None and file_bytes is not None:
        try:
            register_slice(
                case_id=cleaned_id,
                slice_index=1,
                file_name=file_name,
                file_bytes=file_bytes,
                uploaded_by=created_by.strip(),
                image_dir=target_root,
                firestore_client=firestore_client,
                local_images_db_path=local_images_db_path,
                data_dir=base_dir,
            )
        except Exception:
            if firestore_client is not None:
                firestore_client.collection("cases").document(cleaned_id).delete()
            else:
                rollback_cases = _load_json_dict(db_path)
                rollback_cases.pop(cleaned_id, None)
                _save_json_dict(rollback_cases, db_path)
            raise

    return case_data


def list_cases(
    firestore_client=None,
    local_db_path: Path | None = None,
) -> list[dict]:
    """Firestore 또는 로컬 JSON 저장소에서 전체 케이스 목록을 조회한다."""
    if firestore_client is not None:
        docs = firestore_client.collection("cases").stream()
        cases = []
        for doc in docs:
            data = doc.to_dict() if hasattr(doc, "to_dict") else dict(doc)
            data.setdefault("case_id", getattr(doc, "id", data.get("case_id", "")))
            cases.append(data)
        return cases

    db_path = (
        Path(local_db_path)
        if local_db_path is not None
        else (get_base_data_dir() / "cases_local.json")
    )
    local_cases = _load_json_dict(db_path)
    return list(local_cases.values())


def search_cases(
    keyword: str = "",
    status: str | None = None,
    body_part: str | None = None,
    created_by: str | None = None,
    assignee: str | None = None,
    unassigned_only: bool = False,
    firestore_client=None,
    local_db_path: Path | None = None,
) -> list[dict]:
    """키워드(case_id, title) 및 상태·부위·등록자·담당자·미배정 조건으로 케이스를 검색·필터링한다."""
    cases = list_cases(firestore_client=firestore_client, local_db_path=local_db_path)
    kw = keyword.strip().lower()

    results = []
    for case in cases:
        if kw:
            cid = str(case.get("case_id", "")).lower()
            title = str(case.get("title", "")).lower()
            if kw not in cid and kw not in title:
                continue

        if status and case.get("status") != status:
            continue

        if body_part and str(case.get("body_part", "")).upper() != body_part.strip().upper():
            continue

        if created_by and case.get("created_by") != created_by:
            continue

        if unassigned_only:
            if str(case.get("assignee") or "").strip() != "":
                continue
        elif assignee is not None and assignee != "" and case.get("assignee") != assignee:
            continue

        results.append(case)

    results.sort(key=lambda c: c.get("created_at", ""), reverse=True)
    return results

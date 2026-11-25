import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from modules.case_repository import get_base_data_dir
from modules.permissions import can_edit

COLLECTION = "memos"
MEMO_TYPES = {"memo": "메모", "report": "검토 소견"}
MAX_LENGTH = 1000


def _now_utc_z() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _local_path(local_db_path) -> Path:
    if local_db_path is not None:
        return Path(local_db_path)
    return get_base_data_dir() / "memos_local.json"


def _load_local(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _save_local(records: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")


def add_memo(role, uid, case, content, memo_type="memo", image_id=None,
             firestore_client=None, local_db_path=None) -> dict:
    content = (content or "").strip()
    if not content:
        raise ValueError("내용을 입력하세요.")
    if len(content) > MAX_LENGTH:
        raise ValueError(f"{MAX_LENGTH}자 이하로 입력하세요.")
    if memo_type not in MEMO_TYPES:
        raise ValueError(f"메모 종류가 올바르지 않습니다: {memo_type}")

    if not can_edit(role, uid, case):
        raise PermissionError("이 케이스에 메모를 남길 권한이 없습니다.")
    # 검토 소견은 배정된 검토 담당(또는 관리 담당)만 작성
    if memo_type == "report" and role not in ("reviewer", "admin"):
        raise PermissionError("검토 소견은 검토 담당만 작성할 수 있습니다.")

    memo = {
        "case_id": case["case_id"],
        "image_id": image_id,
        "type": memo_type,
        "content": content,
        "created_by": uid,
        "created_at": _now_utc_z(),
    }
    memo_id = uuid.uuid4().hex

    # 수정·삭제 함수는 일부러 만들지 않음 (추가만 가능한 기록)
    if firestore_client is not None:
        firestore_client.collection(COLLECTION).document(memo_id).set(memo)
    else:
        path = _local_path(local_db_path)
        records = _load_local(path)
        records[memo_id] = memo
        _save_local(records, path)

    return {"memo_id": memo_id, **memo}


def list_memos(case_id, firestore_client=None, local_db_path=None) -> list[dict]:
    if firestore_client is not None:
        records = {doc.id: doc.to_dict() for doc in firestore_client.collection(COLLECTION).stream()}
    else:
        records = _load_local(_local_path(local_db_path))

    memos = [{"memo_id": i, **m} for i, m in records.items() if m.get("case_id") == case_id]
    return sorted(memos, key=lambda m: m["created_at"], reverse=True)
"""처리 이력(process_logs) 저장·조회 (역할 C).

case_repository와 같은 방식: firestore_client가 있으면 Firestore,
없으면 로컬 JSON 파일(테스트, secrets 없는 PC용)에 저장한다.
"""
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from modules.case_repository import get_base_data_dir
from modules.permissions import can_edit

COLLECTION = "process_logs"
LOCAL_LOGS_NAME = "process_logs_local.json"


def _now_utc_z() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _local_logs_path(local_db_path):
    """테스트가 경로를 넘기면 그걸 쓰고, 아니면 호출할 때 data_dir 설정을 따른다."""
    if local_db_path is not None:
        return Path(local_db_path)
    return get_base_data_dir() / LOCAL_LOGS_NAME


def _load_local(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _save_local(records: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")


def save_process_log(
    role,
    uid,
    case,
    image_id,
    algorithm,
    algorithm_version,
    params,
    roi,
    result_path,
    metrics,
    firestore_client=None,
    local_db_path=None,
) -> dict:
    """처리 결과 한 건을 저장하고, 저장한 기록(log_id 포함)을 돌려준다.

    권한이 없으면 PermissionError. result_path는 data_dir 기준 상대 경로만 받는다(paths.data_path와 같은 규칙).
    """
    if not can_edit(role, uid, case):
        raise PermissionError("이 케이스에 처리 이력을 저장할 권한이 없습니다.")
    rel_path = Path(result_path)
    if rel_path.anchor or ".." in rel_path.parts:
        raise ValueError("result_path는 data_dir 기준 상대 경로여야 합니다. (절대 경로, .. 사용 불가)")

    log = {
        "case_id": case["case_id"],
        "image_id": image_id,
        "algorithm": algorithm,
        "algorithm_version": algorithm_version,
        "params": dict(params),
        "roi": dict(roi) if roi is not None else None,
        "result_path": Path(result_path).as_posix(),
        "metrics": dict(metrics),
        "run_by": uid,
        "created_at": _now_utc_z(),
    }
    log_id = uuid.uuid4().hex

    if firestore_client is not None:
        firestore_client.collection(COLLECTION).document(log_id).set(log)
    else:
        path = _local_logs_path(local_db_path)
        records = _load_local(path)
        records[log_id] = log
        _save_local(records, path)

    return {"log_id": log_id, **log}


def list_process_logs(image_id, firestore_client=None, local_db_path=None) -> list[dict]:
    """한 영상의 처리 이력을 최신순으로 돌려준다."""
    if firestore_client is not None:
        docs = firestore_client.collection(COLLECTION).stream()
        records = {doc.id: doc.to_dict() for doc in docs}
    else:
        records = _load_local(_local_logs_path(local_db_path))

    logs = [{"log_id": log_id, **log} for log_id, log in records.items() if log.get("image_id") == image_id]
    return sorted(logs, key=lambda log: log["created_at"], reverse=True)

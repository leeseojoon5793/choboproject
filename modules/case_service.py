import json
from datetime import datetime, timezone
from pathlib import Path

from modules.case_repository import search_cases
from modules.paths import get_data_dir
from modules.permissions import can_change_status, can_view


def _now_utc_z() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _save(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def list_visible_cases(db, role, uid, local_db_path=None, **filters) -> list[dict]:
    cases = search_cases(firestore_client=db, local_db_path=local_db_path, **filters)
    return [c for c in cases if can_view(role, uid, c)]


def change_status(db, role, uid, case_id, new_status, reason="", assignee="",
                  data_dir=None) -> tuple[bool, str]:
    reason = (reason or "").strip()
    assignee = (assignee or "").strip()
    if new_status == "assigned" and not assignee:
        return False, "배정할 검토 담당을 선택하세요."
    if new_status == "recheck" and not reason:
        return False, "재검토 요청 사유를 입력하세요."

    base = Path(data_dir) if data_dir is not None else get_data_dir()
    cases_path = base / "cases_local.json"
    logs_path = base / "status_logs_local.json"

    if db is not None:
        case_ref = db.collection("cases").document(case_id)
        snap = case_ref.get()
        case = snap.to_dict() if snap.exists else None
    else:
        local_cases = _load(cases_path)
        case = local_cases.get(case_id)
    if case is None:
        return False, f"케이스를 찾을 수 없습니다: {case_id}"

    ok, msg = can_change_status(role, uid, case, new_status)
    if not ok:
        return False, msg
    old_status = case["status"]
    now = _now_utc_z()
    updates = {"status": new_status, "updated_at": now}
    if new_status == "assigned":
        updates["assignee"] = assignee
    log = {
        "case_id": case_id,
        "from_status": old_status,
        "to_status": new_status,
        "changed_by": uid,
        "reason": reason,
        "created_at": now,
    }

    if db is not None:
        # 상태 변경과 이력 기록이 둘 다 되거나 둘 다 안 되게 한 번에 저장
        batch = db.batch()
        batch.update(case_ref, updates)
        batch.set(db.collection("status_logs").document(), log)
        batch.commit()
    else:
        local_cases[case_id].update(updates)
        logs = _load(logs_path)
        logs[f"{case_id}_{len(logs) + 1:04d}"] = log
        _save(cases_path, local_cases)
        _save(logs_path, logs)

    return True, f"상태를 {old_status}에서 {new_status}(으)로 바꿨습니다."
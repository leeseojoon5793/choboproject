# 상태 변경 규칙: (현재 상태, 바꿀 상태) -> 바꿀 수 있는 역할
TRANSITIONS = {
    ("received", "assigned"): {"admin"},
    ("assigned", "in_review"): {"reviewer"},
    ("in_review", "done"): {"reviewer"},
    ("in_review", "recheck"): {"reviewer"},
    ("recheck", "received"): {"register"},
    ("done", "in_review"): {"admin"},
}


def can_view(role, uid, case):
    if role in ("admin", "reviewer"):
        return True
    return case["created_by"] == uid


def can_edit(role, uid, case):
    if role == "admin":
        return True
    if role == "reviewer":
        return case.get("assignee") == uid
    return case["created_by"] == uid


def can_change_status(role, uid, case, new_status):
    key = (case["status"], new_status)
    if key not in TRANSITIONS:
        return False, f"{case['status']}에서 {new_status}(으)로 바꿀 수 없습니다."
    if role not in TRANSITIONS[key]:
        return False, "이 상태 변경 권한이 없습니다."
    # 역할이 맞아도 자기 케이스가 아니면 막는다
    if role != "admin" and not can_edit(role, uid, case):
        return False, "본인 담당 케이스가 아닙니다."
    return True, ""
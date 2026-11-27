import streamlit as st

from modules.case_service import change_status, list_reviewers
from modules.permissions import TRANSITIONS, can_change_status

STATUS_LABELS = {
    "received": "접수",
    "assigned": "배정됨",
    "in_review": "검토 중",
    "done": "검토 완료",
    "recheck": "재검토 요청",
}

ACTION_LABELS = {
    ("received", "assigned"): "검토 담당 배정",
    ("assigned", "in_review"): "검토 시작",
    ("in_review", "done"): "검토 완료",
    ("in_review", "recheck"): "재검토 요청",
    ("recheck", "received"): "다시 접수",
    ("done", "in_review"): "완료 취소 (다시 검토)",
}


def allowed_actions(role, uid, case) -> list[str]:
    result = []
    for src, dst in TRANSITIONS:
        if src == case["status"] and can_change_status(role, uid, case, dst)[0]:
            result.append(dst)
    return result


def status_panel(db, role, uid, case):
    # 변경 후 st.rerun()을 하면 메시지가 사라져서 session_state에 잠깐 보관
    msg = st.session_state.pop("status_msg", None)
    if msg:
        st.success(msg)

    st.write(f"현재 상태: **{STATUS_LABELS.get(case['status'], case['status'])}**")
    if case.get("assignee"):
        st.caption(f"검토 담당: {case['assignee']}")

    actions = allowed_actions(role, uid, case)
    if not actions:
        st.caption("지금 바꿀 수 있는 상태가 없습니다.")
        return

    for new_status in actions:
        label = ACTION_LABELS[(case["status"], new_status)]
        with st.form(f"status_{case['case_id']}_{new_status}"):
            assignee = ""
            reason = ""
            if new_status == "assigned":
                reviewers = list_reviewers(db)
                if not reviewers:
                    st.warning("등록된 검토 담당 계정이 없습니다.")
                else:
                    picked = st.selectbox("검토 담당", reviewers, format_func=lambda r: r["email"])
                    assignee = picked["uid"]
            if new_status == "recheck":
                reason = st.text_area("재검토 요청 사유")
            submitted = st.form_submit_button(label)

        if submitted:
            ok, result = change_status(db, role, uid, case["case_id"], new_status,
                                       reason=reason, assignee=assignee)
            if ok:
                st.session_state["status_msg"] = result
                st.rerun()
            else:
                st.error(result)
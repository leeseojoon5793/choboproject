import json

import streamlit as st

from modules.db import get_db_or_none
from modules.case_service import list_visible_cases, change_status
from modules.memo import add_memo, list_memos
from modules.paths import get_data_dir


STATUS_LABELS = {
    "received": "검토 대기",
    "assigned": "담당자 배정",
    "in_review": "검토 중",
    "done": "검토 완료",
    "recheck": "재검토 요청",
}


def get_reviewers(db):
    if db is None:
        return {"fake-reviewer": "개발용 검토 담당"}

    reviewers = {}

    try:
        users = db.collection("users").stream()

        for user in users:
            data = user.to_dict()

            if data.get("role") == "reviewer":
                reviewers[user.id] = data.get("name", user.id)

    except Exception as e:
        st.error(f"검토 담당자 목록을 불러오지 못했습니다: {e}")

    return reviewers


def get_status_logs(db, case_id):
    if db is not None:
        try:
            logs = db.collection("status_logs").stream()

            result = [
                log.to_dict()
                for log in logs
                if log.to_dict().get("case_id") == case_id
            ]

            return sorted(
                result,
                key=lambda x: x.get("created_at", ""),
                reverse=True
            )

        except Exception as e:
            st.error(f"변경 이력을 불러오지 못했습니다: {e}")
            return []

    log_path = get_data_dir() / "status_logs_local.json"

    if not log_path.exists():
        return []

    try:
        logs = json.loads(log_path.read_text(encoding="utf-8"))

        return sorted(
            [
                log for log in logs.values()
                if log.get("case_id") == case_id
            ],
            key=lambda x: x.get("created_at", ""),
            reverse=True
        )

    except (json.JSONDecodeError, OSError):
        return []


def show_case_lists(uid, role):
    db = get_db_or_none()
    cases = list_visible_cases(db, role, uid)

    st.header("CT 영상 검토 목록")

    if not cases:
        st.info("현재 표시할 검토 목록이 없습니다.")
        return

    reviewers = get_reviewers(db)

    for case in cases:
        case_id = case.get("case_id", "unknown")
        status = case.get("status", "received")

        with st.expander(
            f"{case.get('title', case_id)} | {case_id}"
        ):
            st.write(f"검사 부위: {case.get('body_part', '-')}")
            st.write(f"제조사: {case.get('manufacturer', '-')}")
            st.write(f"모델: {case.get('model', '-')}")
            st.write(f"상태: {STATUS_LABELS.get(status, status)}")
            st.write(
                f"담당자: {reviewers.get(case.get('assignee'), case.get('assignee') or '미배정')}"
            )

            if role == "admin" and status == "received":
                reviewer_ids = list(reviewers.keys())

                if reviewer_ids:
                    selected_uid = st.selectbox(
                        "검토 담당자 선택",
                        reviewer_ids,
                        format_func=lambda x: reviewers[x],
                        key=f"assignee_{case_id}"
                    )

                    if st.button(
                        "담당자 배정",
                        key=f"assign_{case_id}"
                    ):
                        success, message = change_status(
                            db,
                            role,
                            uid,
                            case_id,
                            "assigned",
                            assignee=selected_uid
                        )

                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)

            if role == "reviewer" and status == "assigned":
                if st.button(
                    "검토 시작",
                    key=f"start_{case_id}"
                ):
                    success, message = change_status(
                        db, role, uid, case_id, "in_review"
                    )

                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)

            st.subheader("메모")

            memo_content = st.text_area(
                "메모 내용",
                key=f"memo_{case_id}"
            )

            if st.button(
                "메모 저장",
                key=f"save_memo_{case_id}"
            ):
                try:
                    add_memo(
                        role,
                        uid,
                        case,
                        memo_content,
                        memo_type="memo",
                        firestore_client=db
                    )
                    st.success("메모가 저장되었습니다.")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))

            st.subheader("검토 소견")

            report_content = st.text_area(
                "검토 소견 작성",
                key=f"report_{case_id}"
            )

            if st.button(
                "소견 저장",
                key=f"save_report_{case_id}"
            ):
                try:
                    add_memo(
                        role,
                        uid,
                        case,
                        report_content,
                        memo_type="report",
                        firestore_client=db
                    )
                    st.success("검토 소견이 저장되었습니다.")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))

            st.subheader("품질 점검 사유")

            quality_reason = st.text_area(
                "품질 점검 사유 입력",
                key=f"quality_reason_{case_id}"
            )

            if st.button(
                "품질 점검 사유 저장",
                key=f"save_quality_{case_id}"
            ):
                try:
                    add_memo(
                        role,
                        uid,
                        case,
                        f"[품질 점검 사유] {quality_reason}",
                        memo_type="memo",
                        firestore_client=db
                    )
                    st.success("품질 점검 사유가 저장되었습니다.")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))

            if role == "reviewer" and status == "in_review":
                recheck_reason = st.text_input(
                    "재검토 요청 사유",
                    key=f"recheck_reason_{case_id}"
                )

                if st.button(
                    "재검토 요청",
                    key=f"recheck_{case_id}"
                ):
                    success, message = change_status(
                        db,
                        role,
                        uid,
                        case_id,
                        "recheck",
                        reason=recheck_reason
                    )

                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)

                if st.button(
                    "검토 완료",
                    key=f"done_{case_id}"
                ):
                    success, message = change_status(
                        db, role, uid, case_id, "done"
                    )

                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)

            st.subheader("저장된 메모 및 소견")

            memos = list_memos(
                case_id,
                firestore_client=db
            )

            if memos:
                for memo in memos:
                    memo_type = memo.get("memo_type", "memo")
                    label = "검토 소견" if memo_type == "report" else "메모"

                    st.write(
                        f"**{label}**: {memo.get('content', '')}"
                    )

                    st.caption(
                        f"작성자: {memo.get('created_by', '-')} | "
                        f"작성일: {memo.get('created_at', '-')}"
                    )
            else:
                st.info("저장된 메모가 없습니다.")

            st.subheader("변경 이력")

            logs = get_status_logs(db, case_id)

            if logs:
                for log in logs:
                    st.write(
                        f"{log.get('from_status', '-')} → "
                        f"{log.get('to_status', '-')}"
                    )

                    st.caption(
                        f"변경 사유: {log.get('reason', '-')} | "
                        f"변경일: {log.get('created_at', '-')}"
                    )
            else:
                st.info("변경 이력이 없습니다.")

    st.divider()

    waiting_cases = [
        case for case in cases
        if case.get("status") in {
            "received", "assigned", "in_review", "recheck"
        }
    ]

    done_cases = [
        case for case in cases
        if case.get("status") == "done"
    ]

    tab1, tab2 = st.tabs(["대기 목록", "완료 목록"])

    with tab1:
        for case in waiting_cases:
            st.write(
                f"{case.get('case_id')} - {case.get('title', '-')}"
            )

    with tab2:
        for case in done_cases:
            st.write(
                f"{case.get('case_id')} - {case.get('title', '-')}"
            )
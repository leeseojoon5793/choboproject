import streamlit as st
from datetime import datetime


def show_case_lists():
    st.header("CT 영상 검토 목록")

    if "cases" not in st.session_state:
        st.session_state["cases"] = [
            {
                "검사 번호": "CT-001",
                "검사 종류": "Chest CT",
                "상태": "검토 대기",
                "담당자": "미배정"
            },
            {
                "검사 번호": "CT-002",
                "검사 종류": "Chest CT",
                "상태": "검토 대기",
                "담당자": "미배정"
            },
            {
                "검사 번호": "CT-003",
                "검사 종류": "Chest CT",
                "상태": "검토 대기",
                "담당자": "미배정"
            },
            {
                "검사 번호": "CT-004",
                "검사 종류": "Chest CT",
                "상태": "검토 완료",
                "담당자": "reviewer"
            }
        ]

    cases = st.session_state["cases"]

    reviewer_options = [
        "미배정",
        "register",
        "reviewer",
        "admin"
    ]

    st.subheader("CT 영상 관리")

    for case in cases:
        case.setdefault("메모", "")
        case.setdefault("리포트", "")
        case.setdefault("품질 점검 사유", "")
        case.setdefault("재검토 상태", "요청 없음")
        case.setdefault("변경 이력", [])

        with st.container(border=True):
            st.subheader(case["검사 번호"])

            st.write(f"검사 종류: {case['검사 종류']}")
            st.write(f"상태: {case['상태']}")

            old_assignee = case["담당자"]

            selected = st.selectbox(
                "담당자 선택",
                reviewer_options,
                index=reviewer_options.index(old_assignee),
                key=f"assignee_{case['검사 번호']}"
            )

            if selected != old_assignee:
                case["담당자"] = selected

                case["변경 이력"].append(
                    f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} "
                    f"담당자 변경: {old_assignee} → {selected}"
                )

            st.write(f"현재 담당자: {case['담당자']}")

            with st.expander("메모 및 리포트"):
                case["메모"] = st.text_area(
                    "검토 메모",
                    value=case["메모"],
                    key=f"memo_{case['검사 번호']}"
                )

                case["리포트"] = st.text_area(
                    "품질 점검 리포트",
                    value=case["리포트"],
                    key=f"report_{case['검사 번호']}"
                )

            with st.expander("품질 점검 사유"):
                case["품질 점검 사유"] = st.text_area(
                    "품질 점검이 필요한 이유",
                    value=case["품질 점검 사유"],
                    key=f"reason_{case['검사 번호']}",
                    placeholder="예: 영상의 밝기가 낮아 세부 구조 확인이 어려움"
                )

                if case["품질 점검 사유"]:
                    st.warning(
                        f"점검 사유: {case['품질 점검 사유']}"
                    )
                else:
                    st.info("등록된 품질 점검 사유가 없습니다.")

            with st.expander("재검토 요청"):
                st.write(
                    f"현재 재검토 상태: {case['재검토 상태']}"
                )

                if st.button(
                    "재검토 요청하기",
                    key=f"recheck_{case['검사 번호']}"
                ):
                    old_status = case["재검토 상태"]
                    case["재검토 상태"] = "재검토 요청"

                    case["변경 이력"].append(
                        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} "
                        f"재검토 상태 변경: {old_status} → 재검토 요청"
                    )

                    st.rerun()

                if case["재검토 상태"] == "재검토 요청":
                    st.warning("재검토가 요청된 영상입니다.")

            with st.expander("변경 이력"):
                if case["변경 이력"]:
                    for history in case["변경 이력"]:
                        st.write(history)
                else:
                    st.write("아직 변경 이력이 없습니다.")

    st.divider()

    waiting_tab, completed_tab = st.tabs(
        ["대기 목록", "완료 목록"]
    )

    with waiting_tab:
        waiting_cases = [
            case for case in cases
            if case["상태"] == "검토 대기"
        ]

        st.subheader("검토 대기 영상")
        st.write(f"대기 중인 영상: {len(waiting_cases)}건")
        st.table(waiting_cases)

    with completed_tab:
        completed_cases = [
            case for case in cases
            if case["상태"] == "검토 완료"
        ]

        st.subheader("검토 완료 영상")
        st.write(f"완료된 영상: {len(completed_cases)}건")
        st.table(completed_cases)
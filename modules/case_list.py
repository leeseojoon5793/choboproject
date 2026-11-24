import streamlit as st


def show_case_lists():
    st.header("CT 영상 검토 목록")

    waiting_cases = [
        {
            "검사 번호": "CT-001",
            "검사 종류": "Chest CT",
            "상태": "검토 대기"
        },
        {
            "검사 번호": "CT-002",
            "검사 종류": "Chest CT",
            "상태": "검토 대기"
        },
        {
            "검사 번호": "CT-003",
            "검사 종류": "Chest CT",
            "상태": "검토 대기"
        }
    ]

    completed_cases = [
        {
            "검사 번호": "CT-004",
            "검사 종류": "Chest CT",
            "상태": "검토 완료"
        }
    ]

    waiting_tab, completed_tab = st.tabs(
        ["대기 목록", "완료 목록"]
    )

    with waiting_tab:
        st.subheader("검토 대기 영상")
        st.write(f"대기 중인 영상: {len(waiting_cases)}건")
        st.table(waiting_cases)

    with completed_tab:
        st.subheader("검토 완료 영상")
        st.write(f"완료된 영상: {len(completed_cases)}건")
        st.table(completed_cases)
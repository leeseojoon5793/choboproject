import streamlit as st

ROLES = {"register": "등록 담당", "reviewer": "검토 담당", "admin": "관리 담당"}


def login_box():
    with st.sidebar:
        if "uid" in st.session_state:
            st.write(f"로그인: {ROLES[st.session_state['role']]}")
            if st.button("로그아웃"):
                logout()
                st.rerun()
            return
        # 진짜 Firebase 로그인이 붙기 전까지 쓰는 개발용 로그인
        st.caption("개발용 가짜 로그인")
        role = st.selectbox("역할", list(ROLES), format_func=lambda r: ROLES[r])
        if st.button("로그인"):
            st.session_state["uid"] = f"fake-{role}"
            st.session_state["role"] = role
            st.rerun()


def logout():
    st.session_state.pop("uid", None)
    st.session_state.pop("role", None)


def require_login():
    login_box()
    if "uid" not in st.session_state:
        st.info("왼쪽에서 로그인하세요.")
        st.stop()
    return st.session_state["uid"], st.session_state["role"]
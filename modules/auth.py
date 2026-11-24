import streamlit as st

from modules import firebase_client

ROLES = {"register": "등록 담당", "reviewer": "검토 담당", "admin": "관리 담당"}


def _firebase_settings():
    # secrets.toml이 없는 팀원 PC에서는 가짜 로그인으로 동작
    try:
        return st.secrets["firebase_api_key"], st.secrets["service_account_path"]
    except (FileNotFoundError, KeyError):
        return None


def _fake_login():
    st.caption("개발용 가짜 로그인 (Firebase 설정 없음)")
    role = st.selectbox("역할", list(ROLES), format_func=lambda r: ROLES[r])
    if st.button("로그인"):
        st.session_state["uid"] = f"fake-{role}"
        st.session_state["role"] = role
        st.rerun()


def _firebase_login(api_key, sa_path):
    email = st.text_input("이메일")
    password = st.text_input("비밀번호", type="password")
    if st.button("로그인"):
        uid = firebase_client.sign_in(api_key, email, password)
        if uid is None:
            st.error("이메일 또는 비밀번호가 틀렸습니다.")
            return
        role = firebase_client.get_role(firebase_client.get_db(sa_path), uid)
        if role not in ROLES:
            st.error("역할이 등록되지 않은 계정입니다. 관리자에게 문의하세요.")
            return
        st.session_state["uid"] = uid
        st.session_state["role"] = role
        st.session_state["email"] = email
        st.rerun()


def login_box():
    with st.sidebar:
        if "uid" in st.session_state:
            who = st.session_state.get("email", st.session_state["uid"])
            st.write(f"{who} ({ROLES[st.session_state['role']]})")
            if st.button("로그아웃"):
                logout()
                st.rerun()
            return
        settings = _firebase_settings()
        if settings is None:
            _fake_login()
        else:
            _firebase_login(*settings)


def logout():
    for key in ("uid", "role", "email"):
        st.session_state.pop(key, None)


def require_login():
    login_box()
    if "uid" not in st.session_state:
        st.info("왼쪽에서 로그인하세요.")
        st.stop()
    return st.session_state["uid"], st.session_state["role"]
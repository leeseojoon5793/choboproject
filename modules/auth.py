import streamlit as st

from modules import firebase_client

ROLES = {"register": "등록 담당", "reviewer": "검토 담당", "admin": "관리 담당"}
ROLE_COLORS = {"register": "blue", "reviewer": "green", "admin": "violet"}

APP_NAME = "흉부 CT 검토 시스템"
APP_DESC = "저선량 흉부 CT 영상 등록 · 검토 · 화질 개선"
NOTICE = "교육·연구용 프로토타입입니다. 진단 목적으로 사용할 수 없으며 공개 데이터셋(TCIA LDCT)만 다룹니다."


def _firebase_settings():
    # secrets.toml이 없는 팀원 PC에서는 가짜 로그인으로 동작
    try:
        return st.secrets["firebase_api_key"], st.secrets["service_account_path"]
    except (FileNotFoundError, KeyError):
        return None


def _fake_login():
    st.caption("개발 모드: Firebase 설정이 없어 역할만 골라 로그인합니다.")
    with st.form("fake_login", border=False):
        role = st.selectbox("역할", list(ROLES), format_func=lambda r: ROLES[r])
        submitted = st.form_submit_button("로그인", type="primary", width="stretch")
    if submitted:
        st.session_state["uid"] = f"fake-{role}"
        st.session_state["role"] = role
        st.rerun()


def _firebase_login(api_key, sa_path):
    with st.form("login", border=False):
        email = st.text_input("이메일", placeholder="name@example.com")
        password = st.text_input("비밀번호", type="password")
        submitted = st.form_submit_button("로그인", type="primary", width="stretch")
    if not submitted:
        return

    email = email.strip()
    if not email or not password:
        st.error("이메일과 비밀번호를 입력하세요.")
        return
    with st.spinner("로그인 중..."):
        uid = firebase_client.sign_in(api_key, email, password)
        if uid is None:
            st.error("이메일 또는 비밀번호가 올바르지 않습니다.")
            return
        role = firebase_client.get_role(firebase_client.get_db(sa_path), uid)
    if role not in ROLES:
        st.error("역할이 등록되지 않은 계정입니다. 관리 담당에게 문의하세요.")
        return
    st.session_state["uid"] = uid
    st.session_state["role"] = role
    st.session_state["email"] = email
    st.rerun()


def _login_screen():
    _, center, _ = st.columns([0.8, 2, 0.8])
    with center:
        st.space("large")
        with st.container(border=True):
            st.subheader(APP_NAME)
            st.caption(APP_DESC)
            settings = _firebase_settings()
            if settings is None:
                _fake_login()
            else:
                _firebase_login(*settings)
        st.caption(NOTICE)


def _user_card():
    role = st.session_state["role"]
    with st.sidebar:
        with st.container(border=True):
            st.markdown(f"**{st.session_state.get('email', st.session_state['uid'])}**")
            st.badge(ROLES[role], color=ROLE_COLORS[role])
            if st.button("로그아웃", width="stretch"):
                logout()
                st.rerun()
        st.caption(NOTICE)


def login_box():
    if "uid" in st.session_state:
        _user_card()
    else:
        _login_screen()


def logout():
    for key in ("uid", "role", "email"):
        st.session_state.pop(key, None)


def require_login():
    login_box()
    if "uid" not in st.session_state:
        st.stop()
    return st.session_state["uid"], st.session_state["role"]    
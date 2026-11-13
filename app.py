import streamlit as st

from modules.auth import ROLES, require_login

st.title("교육용 PACS")

uid, role = require_login()
st.write(f"{ROLES[role]}로 로그인됨 (uid: {uid})")
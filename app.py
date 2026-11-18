import streamlit as st

from modules.auth import ROLES, require_login
from modules.case_list import show_case_lists

st.title("교육용 PACS")

uid, role = require_login()

st.write(f"{ROLES[role]}로 로그인됨 (uid: {uid})")

show_case_lists()
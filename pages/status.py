import streamlit as st

from modules.auth import require_login
from modules.case_service import list_visible_cases
from modules.db import get_db_or_none
from modules.status_ui import STATUS_LABELS, status_panel

st.title("케이스 상태 관리")

uid, role = require_login()
db = get_db_or_none()

status_filter = st.selectbox("상태", ["all"] + list(STATUS_LABELS),
                             format_func=lambda s: "전체" if s == "all" else STATUS_LABELS[s])
filters = {} if status_filter == "all" else {"status": status_filter}
cases = list_visible_cases(db, role, uid, **filters)
if not cases:
    st.info("볼 수 있는 케이스가 없습니다.")
    st.stop()

by_id = {c["case_id"]: c for c in cases}
case_id = st.selectbox(
    "케이스", list(by_id),
    format_func=lambda i: f"{i} | {by_id[i].get('title', '')} | {STATUS_LABELS.get(by_id[i]['status'], by_id[i]['status'])}",
)
status_panel(db, role, uid, by_id[case_id])
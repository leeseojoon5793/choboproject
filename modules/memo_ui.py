import streamlit as st

from modules.memo import MEMO_TYPES, add_memo, list_memos
from modules.permissions import can_edit


def memo_panel(db, role, uid, case):
    st.subheader("메모·검토 소견")

    if can_edit(role, uid, case):
        types = ["memo", "report"] if role in ("reviewer", "admin") else ["memo"]
        with st.form(f"memo_{case['case_id']}", clear_on_submit=True):
            memo_type = st.radio("종류", types, format_func=lambda t: MEMO_TYPES[t], horizontal=True)
            content = st.text_area("내용")
            submitted = st.form_submit_button("저장")
        if submitted:
            try:
                add_memo(role, uid, case, content, memo_type=memo_type, firestore_client=db)
                st.success("저장했습니다.")
            except (ValueError, PermissionError) as e:
                st.error(str(e))

    memos = list_memos(case["case_id"], firestore_client=db)
    if not memos:
        st.caption("아직 남긴 메모가 없습니다.")
    for m in memos:
        st.markdown(f"**[{MEMO_TYPES.get(m['type'], m['type'])}]** {m['created_by']} · {m['created_at']}")
        st.text(m["content"])
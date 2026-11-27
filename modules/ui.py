from datetime import datetime, timedelta, timezone

import streamlit as st

KST = timezone(timedelta(hours=9))

STATUS_LABELS = {
    "received": "접수",
    "assigned": "배정됨",
    "in_review": "검토 중",
    "done": "검토 완료",
    "recheck": "재검토 요청",
}
STATUS_COLORS = {
    "received": "gray",
    "assigned": "blue",
    "in_review": "orange",
    "done": "green",
    "recheck": "red",
}
FAKE_USERS = {
    "fake-register": "등록 담당 (개발 모드)",
    "fake-reviewer": "검토 담당 (개발 모드)",
    "fake-admin": "관리 담당 (개발 모드)",
}


def format_time(value) -> str:
    # DB의 UTC 시각("2026-11-27T11:18:00Z")을 한국 시간으로 표시
    if not value:
        return "-"
    try:
        dt = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return str(value)
    return dt.astimezone(KST).strftime("%Y.%m.%d %H:%M")


def status_text(status) -> str:
    return STATUS_LABELS.get(status, status)


def status_badge(status):
    st.badge(status_text(status), color=STATUS_COLORS.get(status, "gray"))


@st.cache_data(ttl=300, show_spinner=False)
def _user_emails(_db) -> dict:
    # 화면이 다시 그려질 때마다 users 전체를 읽지 않도록 5분간 저장
    return {doc.id: doc.to_dict().get("email", doc.id) for doc in _db.collection("users").stream()}


def user_label(db, uid) -> str:
    if not uid:
        return "-"
    if db is None:
        return FAKE_USERS.get(uid, uid)
    return _user_emails(db).get(uid, uid)
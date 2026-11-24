import streamlit as st

from modules import firebase_client


def get_db_or_none():
    # secrets.toml이 없으면 None을 돌려주고, 각 기능은 로컬 JSON 저장으로 동작
    try:
        sa_path = st.secrets["service_account_path"]
    except (FileNotFoundError, KeyError):
        return None
    return firebase_client.get_db(sa_path)
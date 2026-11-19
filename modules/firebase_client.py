import firebase_admin
import requests
from firebase_admin import credentials, firestore

SIGN_IN_URL = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"


def get_db(service_account_path):
    # Streamlit은 화면마다 코드를 다시 실행하므로 앱 초기화는 한 번만
    try:
        firebase_admin.get_app()
    except ValueError:
        firebase_admin.initialize_app(credentials.Certificate(service_account_path))
    return firestore.client()


def sign_in(api_key, email, password):
    res = requests.post(
        SIGN_IN_URL,
        params={"key": api_key},
        json={"email": email, "password": password, "returnSecureToken": True},
        timeout=10,
    )
    if res.status_code != 200:
        return None
    return res.json()["localId"]


def get_role(db, uid):
    doc = db.collection("users").document(uid).get()
    if not doc.exists:
        return None
    return doc.to_dict().get("role")
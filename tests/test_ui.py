from modules import ui


def test_format_time_converts_utc_to_kst():
    assert ui.format_time("2026-11-27T11:18:00Z") == "2026.11.27 20:18"
    assert ui.format_time("2026-11-27T20:30:00Z") == "2026.11.28 05:30"


def test_format_time_handles_empty_and_bad_values():
    assert ui.format_time("") == "-"
    assert ui.format_time(None) == "-"
    assert ui.format_time("어제") == "어제"


def test_status_text():
    assert ui.status_text("in_review") == "검토 중"
    assert ui.status_text("unknown") == "unknown"


def test_user_label_local_mode():
    assert ui.user_label(None, "fake-reviewer") == "검토 담당 (개발 모드)"
    assert ui.user_label(None, "someone") == "someone"
    assert ui.user_label(None, "") == "-"


class _Doc:
    def __init__(self, uid, data):
        self.id = uid
        self._data = data

    def to_dict(self):
        return self._data


class _FakeDb:
    def collection(self, name):
        assert name == "users"
        return self

    def stream(self):
        return [_Doc("U1", {"email": "rev@example.com", "role": "reviewer"})]


def test_user_label_firestore_mode():
    ui._user_emails.clear()
    db = _FakeDb()
    assert ui.user_label(db, "U1") == "rev@example.com"
    assert ui.user_label(db, "U9") == "U9"
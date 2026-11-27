from modules.case_service import list_reviewers
from modules.status_ui import ACTION_LABELS, allowed_actions
from modules.permissions import TRANSITIONS


def test_every_transition_has_button_label():
    assert set(ACTION_LABELS) == set(TRANSITIONS)


def test_admin_sees_assign_only_on_received():
    case = {"status": "received", "created_by": "u-reg", "assignee": ""}
    assert allowed_actions("admin", "u-admin", case) == ["assigned"]
    assert allowed_actions("register", "u-reg", case) == []


def test_reviewer_buttons_only_on_own_case():
    case = {"status": "in_review", "created_by": "u-reg", "assignee": "u-rev"}
    assert sorted(allowed_actions("reviewer", "u-rev", case)) == ["done", "recheck"]
    assert allowed_actions("reviewer", "u-other", case) == []


def test_local_reviewer_matches_fake_login():
    assert list_reviewers(None)[0]["uid"] == "fake-reviewer"
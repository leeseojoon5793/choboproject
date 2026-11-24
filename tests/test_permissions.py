from modules.permissions import can_change_status, can_edit, can_view

CASE = {"status": "in_review", "created_by": "u-reg", "assignee": "u-rev"}


def test_reviewer_can_finish_own_case():
    ok, _ = can_change_status("reviewer", "u-rev", CASE, "done")
    assert ok


def test_reviewer_cannot_finish_other_case():
    ok, msg = can_change_status("reviewer", "u-other", CASE, "done")
    assert not ok and "본인" in msg


def test_register_cannot_finish():
    ok, _ = can_change_status("register", "u-reg", CASE, "done")
    assert not ok


def test_skip_step_rejected():
    case = dict(CASE, status="received")
    ok, _ = can_change_status("admin", "u-admin", case, "done")
    assert not ok


def test_only_admin_reopens_done():
    case = dict(CASE, status="done")
    assert can_change_status("admin", "u-admin", case, "in_review")[0]
    assert not can_change_status("reviewer", "u-rev", case, "in_review")[0]


def test_register_resubmits_own_recheck():
    case = dict(CASE, status="recheck")
    assert can_change_status("register", "u-reg", case, "received")[0]
    assert not can_change_status("register", "u-x", case, "received")[0]


def test_view_and_edit_scope():
    assert can_view("reviewer", "u-other", CASE)
    assert not can_edit("reviewer", "u-other", CASE)
    assert not can_view("register", "u-x", CASE)
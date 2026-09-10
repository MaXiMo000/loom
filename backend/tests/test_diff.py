"""diff_nodes: pure logic, no DB needed — SQLAlchemy model instances work
fine unpersisted for plain attribute access."""

from __future__ import annotations

from app.diff import diff_nodes
from app.models import Node


def _node(**kwargs) -> Node:
    defaults = dict(
        package_name="x", package_version="1.0.0", depth=0,
        vuln_severity="none", drift_status="matched",
        providence_status="unverified", policy_status="unverified",
    )
    defaults.update(kwargs)
    return Node(**defaults)


def test_no_changes_between_identical_scans():
    older = [_node(package_name="flask", package_version="3.0.3")]
    newer = [_node(package_name="flask", package_version="3.0.3")]
    assert diff_nodes(older, newer) == []


def test_added_package():
    older = [_node(package_name="flask")]
    newer = [_node(package_name="flask"), _node(package_name="werkzeug", package_version="3.1.8")]
    changes = diff_nodes(older, newer)
    assert changes == [{
        "package_name": "werkzeug", "change_type": "added",
        "from_version": None, "to_version": "3.1.8",
        "detail": "'werkzeug' 3.1.8 appeared in the resolved graph",
    }]


def test_removed_package():
    older = [_node(package_name="flask"), _node(package_name="werkzeug", package_version="3.1.8")]
    newer = [_node(package_name="flask")]
    changes = diff_nodes(older, newer)
    assert changes == [{
        "package_name": "werkzeug", "change_type": "removed",
        "from_version": "3.1.8", "to_version": None,
        "detail": "'werkzeug' 3.1.8 is no longer in the resolved graph",
    }]


def test_the_headline_scenario_matched_to_version_mismatch():
    # SPEC.md §10's own words: "this package went from matched to
    # version_mismatch between scan N and N+1."
    older = [_node(package_name="urllib3", drift_status="matched")]
    newer = [_node(package_name="urllib3", drift_status="version_mismatch")]
    changes = diff_nodes(older, newer)
    assert changes == [{
        "package_name": "urllib3", "change_type": "changed",
        "from_version": "1.0.0", "to_version": "1.0.0",
        "detail": "drift_status matched → version_mismatch",
    }]


def test_version_bump_and_severity_change_both_reported():
    older = [_node(package_name="urllib3", package_version="2.0.6", vuln_severity="high")]
    newer = [_node(package_name="urllib3", package_version="2.0.7", vuln_severity="none")]
    changes = diff_nodes(older, newer)
    assert len(changes) == 1
    assert "version 2.0.6 → 2.0.7" in changes[0]["detail"]
    assert "vuln_severity high → none" in changes[0]["detail"]


def test_detail_text_changing_alone_is_not_a_reported_change():
    # Same status, different evidence wording -- not part of SIGNAL_FIELDS,
    # so it must not show up as a change.
    older = [_node(package_name="flask", vuln_severity="high", vuln_detail="old wording")]
    newer = [_node(package_name="flask", vuln_severity="high", vuln_detail="new wording")]
    assert diff_nodes(older, newer) == []

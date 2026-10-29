from urllib.error import HTTPError
from unittest.mock import patch

import pytest

from scripts import coordination_status_report as reporter


def pr_payload(head="abc1234567890"):
    return {
        "number": 1,
        "title": "test: verify empty Binance kline response",
        "html_url": "https://github.com/salamou1944/Astra/pull/1",
        "state": "open",
        "draft": False,
        "merged": False,
        "head": {"sha": head},
    }


def test_status_body_is_stable_and_explicitly_non_agentic():
    runs = [{
        "head_sha": "abc1234567890",
        "name": "ASTRA CI",
        "run_number": 210,
        "html_url": "https://github.com/salamou1944/Astra/actions/runs/40631142490",
        "status": "completed",
        "conclusion": "success",
        "created_at": "2026-10-28T04:13:52Z",
    }]
    body = reporter.build_status_body(pr_payload(), runs, "2026-10-28 04:30 UTC")
    assert reporter.MARKER in body
    assert "abc123456789" in body
    assert "completed / success" in body
    assert "does not wake or run Agent #1/#2" in body
    assert "merged: false" in body


def test_synthetic_merge_run_matches_pr_head_via_pull_requests_metadata():
    runs = [{
        "head_sha": "synthetic-merge-sha",
        "pull_requests": [{"head": {"sha": "abc1234567890"}}],
        "name": "ASTRA CI",
        "run_number": 220,
        "html_url": "https://github.com/salamou1944/Astra/actions/runs/123",
        "status": "completed",
        "conclusion": "success",
        "created_at": "2026-10-28T05:00:00Z",
    }]
    assert reporter.select_latest_relevant_run(pr_payload(), runs) == runs[0]
    body = reporter.build_status_body(pr_payload(), runs, "fixed time")
    assert "ASTRA CI #220" in body
    assert "completed / success" in body
    assert "synthetic merge ref" in body.lower()


def test_old_head_run_is_not_misattributed():
    runs = [{
        "head_sha": "old-head-sha",
        "pull_requests": [{"head": {"sha": "older-pr-head"}}],
        "name": "ASTRA CI",
        "run_number": 209,
        "created_at": "2026-10-28T04:00:00Z",
    }]
    assert reporter.select_latest_relevant_run(pr_payload("new-head-sha"), runs) is None
    assert "No CI run matched" in reporter.build_status_body(pr_payload("new-head-sha"), runs)


def test_event_filter_allows_schedule_and_manual_triggers():
    assert reporter.should_process_event("schedule", {}, "")
    assert reporter.should_process_event("workflow_dispatch", {}, "")


def test_event_filter_allows_human_comment_on_canonical_pr_mailbox():
    assert reporter.should_process_event(
        "issue_comment", {"number": 1, "pull_request": {"url": "https://api.github.com/repos/o/r/pulls/1"}}, "human"
    )


@pytest.mark.parametrize("issue,user", [
    ({"number": 2, "pull_request": {"url": "x"}}, "human"),
    ({"number": 1}, "human"),  # ordinary issue, not a pull request
    ({"number": 1, "pull_request": {"url": "x"}}, "github-actions[bot]"),
    ({"number": 1, "pull_request": {"url": "x"}}, "another-bot[bot]"),
    ({"number": 1, "pull_request": {"url": "x"}}, ""),
])
def test_event_filter_rejects_wrong_mailbox_non_pr_and_bot_or_missing_author(issue, user):
    assert not reporter.should_process_event("issue_comment", issue, user)


def test_find_status_comment_ignores_human_comments_that_only_mention_marker():
    comments = [
        {"id": 10, "body": "ordinary comment"},
        {"id": 11, "body": "older " + reporter.MARKER},
        {"id": 12, "body": "discussion about " + reporter.MARKER},
        {"id": 13, "body": reporter.MARKER + "\n## ASTRA coordination status"},
    ]
    assert reporter.find_status_comment(comments)["id"] == 13


def test_api_failure_is_not_silently_reported_as_success():
    error = HTTPError("https://api.github.com/test", 403, "forbidden", {}, None)
    with patch.object(reporter, "urlopen", side_effect=error):
        with pytest.raises(HTTPError):
            reporter.request_json("https://api.github.com/test", "token")


def test_status_comment_update_uses_existing_comment_id():
    with patch.object(reporter, "request_json") as api:
        api.side_effect = [
            [
                {"id": 88, "body": "conversation mentions " + reporter.MARKER},
                {"id": 99, "body": reporter.MARKER + "\n## ASTRA coordination status"},
            ],
            {},
        ]
        result = reporter.publish_status_comment("https://api.github.com/repos/o/r", 1, "token", "new body")
    assert result == "Updated existing status comment #99."
    assert api.call_args_list[1].args[0].endswith("/issues/comments/99")
    assert api.call_args_list[1].kwargs["payload"] == {"body": "new body"}

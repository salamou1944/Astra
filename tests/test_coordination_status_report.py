from pathlib import Path
from tempfile import TemporaryDirectory
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


def test_synthetic_merge_run_is_selected_and_rendered():
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


def test_api_failure_is_not_silently_reported_as_success():
    error = HTTPError("https://api.github.com/test", 403, "forbidden", {}, None)
    with patch.object(reporter, "urlopen", side_effect=error):
        with pytest.raises(HTTPError):
            reporter.request_json("https://api.github.com/test", "token")


def test_status_report_is_written_to_actions_summary():
    with TemporaryDirectory() as tmp:
        path = str(Path(tmp) / "summary.md")
        reporter.write_step_summary("## status one", path)
        reporter.write_step_summary("## status two", path)
        assert Path(path).read_text(encoding="utf-8") == "## status one\n## status two\n"

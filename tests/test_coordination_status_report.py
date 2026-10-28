from scripts.coordination_status_report import MARKER, build_status_body


def test_status_body_is_stable_and_explicitly_non_agentic():
    pr = {
        "number": 1,
        "title": "test: verify empty Binance kline response",
        "html_url": "https://github.com/salamou1944/Astra/pull/1",
        "state": "open",
        "draft": True,
        "merged": False,
        "head": {"sha": "abc1234567890"},
    }
    runs = [{
        "head_sha": "abc1234567890",
        "name": "ASTRA CI",
        "run_number": 210,
        "html_url": "https://github.com/salamou1944/Astra/actions/runs/40631142490",
        "status": "completed",
        "conclusion": "success",
        "created_at": "2026-10-28T04:13:52Z",
    }]
    body = build_status_body(pr, runs, "2026-10-28 04:30 UTC")
    assert MARKER in body
    assert "abc123456789" in body
    assert "completed / success" in body
    assert "does not wake or run Agent #1/#2" in body
    assert "merged: false" in body


def test_status_body_does_not_misattribute_run_from_another_head():
    pr = {
        "number": 1,
        "title": "ASTRA",
        "html_url": "https://github.com/salamou1944/Astra/pull/1",
        "state": "open",
        "draft": True,
        "merged": False,
        "head": {"sha": "new-head-sha"},
    }
    runs = [{
        "head_sha": "old-head-sha",
        "name": "ASTRA CI",
        "run_number": 209,
        "html_url": "https://github.com/salamou1944/Astra/actions/runs/40629039202",
        "status": "completed",
        "conclusion": "success",
        "created_at": "2026-10-28T04:00:00Z",
    }]
    body = build_status_body(pr, runs, "2026-10-28 04:30 UTC")
    assert "No workflow run found for the current PR head yet." in body
    assert "run #209" not in body

#!/usr/bin/env python3
"""Publish a deterministic, read-only status snapshot for ASTRA PR #1."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from urllib.request import Request, urlopen

API = "https://api.github.com"
MARKER = "<!-- astra-coordination-status -->"


def request_json(url: str, token: str):
    req = Request(url, headers={
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "astra-coordination-status",
    })
    # Fail loudly on API/network errors; a failed report must not look successful.
    with urlopen(req, timeout=20) as response:
        raw = response.read()
    return json.loads(raw.decode("utf-8")) if raw else {}


def _run_matches_pr_head(run: dict, head_sha: str) -> bool:
    if run.get("head_sha") == head_sha:
        return True
    # GitHub may run PR workflows against a synthetic refs/pull/<n>/merge SHA.
    return any(
        (pr.get("head") or {}).get("sha") == head_sha
        for pr in (run.get("pull_requests") or [])
    )


def select_latest_relevant_run(pr: dict, runs: list[dict]) -> dict | None:
    head_sha = (pr.get("head") or {}).get("sha", "")
    matching = [run for run in runs if _run_matches_pr_head(run, head_sha)]
    matching.sort(key=lambda run: run.get("created_at", ""), reverse=True)
    return matching[0] if matching else None


def build_status_body(pr: dict, runs: list[dict], timestamp: str | None = None) -> str:
    timestamp = timestamp or datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    head = (pr.get("head") or {}).get("sha", "unknown")
    run = select_latest_relevant_run(pr, runs)
    if run:
        ci = f'[{run.get("name", "GitHub Actions")} #{run.get("run_number", "?")}]({run.get("html_url", "")}) — {run.get("status", "unknown")} / {run.get("conclusion") or "pending"}'
    else:
        ci = "No CI run matched this PR head or its synthetic merge ref in the latest Actions results; verify the PR Checks tab."
    state = pr.get("state", "unknown").upper()
    draft = "yes" if pr.get("draft") else "no"
    return (
        f"{MARKER}\n"
        "## ASTRA coordination status (automated snapshot)\n\n"
        f"- Updated: {timestamp}\n"
        f"- PR: [#{pr.get('number', 1)} — {pr.get('title', 'ASTRA')}]({pr.get('html_url', '')})\n"
        f"- State: {state}; draft: {draft}; merged: {str(bool(pr.get('merged'))).lower()}\n"
        f"- Current head: `{head[:12]}`\n"
        f"- Latest relevant CI (PR head or synthetic merge ref): {ci}\n\n"
        "**Scope:** deterministic GitHub metadata only. This does not wake or run Agent #1/#2, provide AI review, prove profitability, or authorize merging/trading. Read the conversation comments for human/agent handoffs. No secrets are read or printed."
    )


def write_step_summary(body: str, summary_path: str) -> None:
    # GitHub Actions provides this file path; writing it needs no API write scope.
    with open(summary_path, "a", encoding="utf-8") as summary:
        summary.write(body.rstrip() + "\n")


def main() -> None:
    token = os.environ["GITHUB_TOKEN"]
    repo = os.environ["GITHUB_REPOSITORY"]
    pr_number = int(os.environ.get("PR_NUMBER", "1"))
    base = f"{API}/repos/{repo}"
    pr = request_json(f"{base}/pulls/{pr_number}", token)
    # Inspect recent pull_request runs too: their run SHA may be a synthetic merge ref.
    runs_payload = request_json(
        f"{base}/actions/runs?event=pull_request&per_page=100", token
    )
    runs = runs_payload.get("workflow_runs", [])
    body = build_status_body(pr, runs)
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_path:
        raise RuntimeError("GITHUB_STEP_SUMMARY is required; refusing to report success without publishing the status.")
    write_step_summary(body, summary_path)
    head_sha = (pr.get("head") or {}).get("sha", "")
    print(f"Published status report to the GitHub Actions job summary: {summary_path}")
    print(f"PR #{pr_number}; head={head_sha[:12]}; relevant_runs={sum(1 for run in runs if _run_matches_pr_head(run, head_sha))}")


if __name__ == "__main__":
    main()

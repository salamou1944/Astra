#!/usr/bin/env python3
"""Publish a deterministic, no-model status snapshot for ASTRA PR #1.

Uses only GitHub's built-in GITHUB_TOKEN. It does not run an AI agent, trade,
modify repository files, or trigger external paid services.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from urllib.error import HTTPError
from urllib.request import Request, urlopen

API = "https://api.github.com"
MARKER = "<!-- astra-coordination-status -->"


def request_json(url: str, token: str, method: str = "GET", payload: dict | None = None):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = Request(
        url,
        data=data,
        method=method,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
            "User-Agent": "astra-coordination-status",
        },
    )
    with urlopen(req, timeout=20) as response:
        raw = response.read()
    return json.loads(raw.decode("utf-8")) if raw else {}


def build_status_body(pr: dict, runs: list[dict], timestamp: str | None = None) -> str:
    timestamp = timestamp or datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    head = (pr.get("head") or {}).get("sha", "unknown")
    head_short = head[:12]
    matching = [r for r in runs if r.get("head_sha") == head]
    matching.sort(key=lambda r: r.get("created_at", ""), reverse=True)
    if matching:
        run = matching[0]
        ci = f'[{run.get("name", "GitHub Actions")} #{run.get("run_number", "?")}]({run.get("html_url", "")}) — {run.get("status", "unknown")} / {run.get("conclusion") or "pending"}'
    else:
        ci = "No workflow run found for the current PR head yet."
    state = pr.get("state", "unknown").upper()
    draft = "yes" if pr.get("draft") else "no"
    return (
        f"{MARKER}\n"
        "## ASTRA coordination status (automated snapshot)\n\n"
        f"- Updated: {timestamp}\n"
        f"- PR: [#{pr.get('number', 1)} — {pr.get('title', 'ASTRA')}]({pr.get('html_url', '')})\n"
        f"- State: {state}; draft: {draft}; merged: {str(bool(pr.get('merged'))).lower()}\n"
        f"- Current head: `{head_short}`\n"
        f"- Latest CI for this exact head: {ci}\n\n"
        "**Scope:** deterministic GitHub metadata only. This does not wake or run Agent #1/#2, provide AI review, prove profitability, or authorize merging/trading. Read the conversation comments for human/agent handoffs. No secrets are read or printed."
    )


def main() -> None:
    token = os.environ["GITHUB_TOKEN"]
    repo = os.environ["GITHUB_REPOSITORY"]
    pr_number = int(os.environ.get("PR_NUMBER", "1"))
    base = f"{API}/repos/{repo}"
    pr = request_json(f"{base}/pulls/{pr_number}", token)
    head_sha = (pr.get("head") or {}).get("sha", "")
    runs_payload = request_json(
        f"{base}/actions/runs?head_sha={head_sha}&per_page=20", token
    )
    runs = runs_payload.get("workflow_runs", [])
    body = build_status_body(pr, runs)

    comments = request_json(f"{base}/issues/{pr_number}/comments?per_page=100", token)
    existing = next(
        (c for c in reversed(comments) if MARKER in (c.get("body") or "")),
        None,
    )
    if existing:
        request_json(
            f"{base}/issues/comments/{existing['id']}",
            token,
            method="PATCH",
            payload={"body": body},
        )
        action = f"Updated existing status comment #{existing['id']}."
    else:
        created = request_json(
            f"{base}/issues/{pr_number}/comments",
            token,
            method="POST",
            payload={"body": body},
        )
        action = f"Created status comment #{created.get('id', 'unknown')}."
    print(action)
    print(f"PR #{pr_number}; head={head_sha[:12]}; matching_runs={len([r for r in runs if r.get('head_sha') == head_sha])}")


if __name__ == "__main__":
    main()

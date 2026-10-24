#!/usr/bin/env python3
"""Select the latest completed encrypted capture without falling back to stale state.

Selection is read-only. The caller must still download the selected artifact and
verify its manifest, encrypted payload, recipient certificate and state provenance.
Passing --handoff-branch explicitly permits a predecessor only when the current
branch has no complete encrypted capture. There is no default-branch fallback.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
import re
import sys
import urllib.error
import urllib.parse
import urllib.request


POLICIES = {
    ".github/workflows/terrafar-source-maintenance.yml": {
        "job": "source-maintenance",
        "steps": (
            "Build a sanitized public report and encrypted candidate checkpoint",
            "Save sanitized diagnostics and encrypted candidate state",
        ),
        "artifact_prefix": "terrafar-source-maintenance-state-v3",
        "format": "terrafar-source-maintenance-public-artifact-v1",
    },
    ".github/workflows/terrafar-full-census.yml": {
        "job": "all-registered-sources",
        "steps": (
            "Export auditable metadata for the review workspace",
            "Preserve public diagnostics and encrypted state checkpoint",
        ),
        "artifact_prefix": "terrafar-full-census",
        "format": "terrafar-full-census-artifact-v1",
    },
}
EVENTS = {"push", "schedule", "workflow_dispatch"}


class SelectionError(ValueError):
    pass


def positive_id(value, label):
    if not re.fullmatch(r"[1-9][0-9]*", str(value)):
        raise SelectionError(f"invalid_{label}")
    return str(value)


def timestamp(value):
    try:
        parsed = dt.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError()
        return parsed.astimezone(dt.timezone.utc)
    except (TypeError, ValueError) as error:
        raise SelectionError("checkpoint_capture_timestamp_invalid") from error


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise SelectionError("github_api_redirect_refused")


class GitHubAPI:
    def __init__(self, repository, token):
        self.repository = repository
        self.token = token
        self.opener = urllib.request.build_opener(NoRedirect())

    def get(self, endpoint):
        request = urllib.request.Request(
            f"https://api.github.com/repos/{self.repository}/{endpoint}",
            headers={"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28",
                     "User-Agent": "TERRAFAR-checkpoint-selector",
                     **({"Authorization": f"Bearer {self.token}"} if self.token else {})},
        )
        try:
            with self.opener.open(request, timeout=45) as response:
                value = json.load(response)
        except urllib.error.HTTPError as error:
            raise SelectionError(f"github_api_http_{error.code}") from None
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            raise SelectionError("github_api_unavailable_or_invalid_json") from None
        if not isinstance(value, dict):
            raise SelectionError("github_api_response_not_object")
        return value

    def pages(self, path, field, parameters=None):
        results = []
        for page in range(1, 101):
            query = urllib.parse.urlencode({**(parameters or {}), "per_page": 100, "page": page})
            response = self.get(f"{path}?{query}")
            rows = response.get(field)
            if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
                raise SelectionError(f"github_api_{field}_malformed")
            results.extend(rows)
            if len(rows) < 100:
                if response.get("total_count", len(results)) > len(results):
                    raise SelectionError(f"github_api_{field}_history_incomplete")
                return results
        raise SelectionError(f"github_api_{field}_pagination_limit")

    def runs(self, branch):
        return self.pages("actions/runs", "workflow_runs", {"branch": branch, "status": "completed"})

    def jobs(self, run_id, attempt):
        return self.pages(f"actions/runs/{run_id}/attempts/{attempt}/jobs", "jobs")

    def artifacts(self, run_id):
        return self.pages(f"actions/runs/{run_id}/artifacts", "artifacts")


def complete_captures(api, repository, branch, current_run_id, maintenance_only=False):
    captures = []
    seen = set()
    for run in api.runs(branch):
        path = run.get("path")
        if (path not in POLICIES or (maintenance_only and path != ".github/workflows/terrafar-source-maintenance.yml")
                or run.get("head_branch") != branch or str(run.get("id")) == current_run_id
                or run.get("status") != "completed" or run.get("event") not in EVENTS):
            continue
        if (run.get("repository", {}).get("full_name") != repository
                or run.get("head_repository", {}).get("full_name") != repository):
            continue
        run_id = positive_id(run.get("id"), "run_id")
        attempt_count = int(positive_id(run.get("run_attempt"), "run_attempt"))
        if run_id in seen:
            raise SelectionError("duplicate_workflow_run_metadata")
        seen.add(run_id)
        policy = POLICIES[path]
        for attempt in range(attempt_count, 0, -1):
            jobs = [job for job in api.jobs(run_id, attempt) if job.get("name") == policy["job"]]
            if len(jobs) > 1:
                raise SelectionError("ambiguous_checkpoint_capture_job")
            if not jobs:
                continue
            job = jobs[0]
            if job.get("run_id") != int(run_id) or job.get("run_attempt") != attempt:
                raise SelectionError("checkpoint_job_origin_mismatch")
            steps = job.get("steps", [])
            matched = [[step for step in steps if step.get("name") == name] for name in policy["steps"]]
            if any(len(group) > 1 for group in matched):
                raise SelectionError("ambiguous_checkpoint_capture_step")
            if any(len(group) != 1 or group[0].get("conclusion") != "success" for group in matched):
                continue
            completed_at = max(timestamp(group[0].get("completed_at")) for group in matched)
            captures.append({"run_id": run_id, "run_attempt": attempt, "branch": branch,
                             "workflow_path": path, "head_sha": run.get("head_sha"),
                             "artifact_name": f"{policy['artifact_prefix']}-{run_id}-{attempt}",
                             "format": policy["format"], "capture_completed_at": completed_at.isoformat(),
                             "workflow_conclusion": run.get("conclusion")})
    return sorted(captures, key=lambda row: (timestamp(row["capture_completed_at"]), int(row["run_id"]), row["run_attempt"]), reverse=True)


def select_checkpoint(api, repository, current_run_id, branch, handoff_branch=None,
                      restore_run_id=None, restore_artifact_name=None):
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise SelectionError("invalid_repository")
    current_run_id = positive_id(current_run_id, "current_run_id")
    for name in (branch, handoff_branch):
        if name is not None and (not name.strip() or any(ord(character) < 32 for character in name)):
            raise SelectionError("invalid_branch")
    if handoff_branch == branch:
        raise SelectionError("handoff_branch_must_differ")
    if bool(restore_run_id) != bool(restore_artifact_name):
        raise SelectionError("explicit_restore_requires_run_and_artifact")
    if restore_run_id:
        restore_run_id = positive_id(restore_run_id, "explicit_restore_run_id")
    captures = complete_captures(api, repository, branch, current_run_id, maintenance_only=True)
    source = "current_branch_latest_complete_capture"
    if not captures and handoff_branch:
        captures = complete_captures(api, repository, handoff_branch, current_run_id)
        source = "explicit_predecessor_handoff"
    if not captures:
        raise SelectionError("no_complete_encrypted_checkpoint_in_authorized_scope")
    selected = captures[0]
    if restore_run_id and (restore_run_id != selected["run_id"] or restore_artifact_name != selected["artifact_name"]):
        raise SelectionError("explicit_restore_is_not_latest_authorized_complete_capture")
    artifacts = [row for row in api.artifacts(selected["run_id"]) if row.get("name") == selected["artifact_name"]]
    if len(artifacts) != 1:
        raise SelectionError("latest_complete_capture_artifact_missing_or_ambiguous_no_rollback")
    artifact = artifacts[0]
    expires = artifact.get("expires_at")
    if artifact.get("expired") is not False or (expires and timestamp(expires) <= dt.datetime.now(dt.timezone.utc)):
        raise SelectionError("latest_complete_capture_artifact_expired_no_rollback")
    origin = artifact.get("workflow_run", {})
    if origin.get("id") != int(selected["run_id"]) or (origin.get("head_branch") and origin["head_branch"] != selected["branch"]):
        raise SelectionError("checkpoint_artifact_origin_mismatch")
    return {**selected, "artifact_id": positive_id(artifact.get("id"), "artifact_id"), "restore_source": source,
            "privacy_requirement": "encrypted_payload_and_manifest_must_be_verified_after_download"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--current-run-id", required=True)
    parser.add_argument("--branch", required=True)
    parser.add_argument("--handoff-branch")
    parser.add_argument("--restore-run-id")
    parser.add_argument("--restore-artifact-name")
    parser.add_argument("--github-output", type=Path)
    args = parser.parse_args()
    try:
        api = GitHubAPI(args.repository, os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN"))
        result = select_checkpoint(api, args.repository, args.current_run_id, args.branch, args.handoff_branch,
                                   args.restore_run_id, args.restore_artifact_name)
        if args.github_output:
            with args.github_output.open("a", encoding="utf-8") as output:
                for key in ("run_id", "run_attempt", "artifact_name", "artifact_id", "format", "branch", "head_sha", "restore_source"):
                    output.write(f"{key}={result[key]}\n")
        print(json.dumps(result, sort_keys=True))
    except SelectionError as error:
        print(f"checkpoint_selection_failed:{error}", file=sys.stderr)
        raise SystemExit(2)


if __name__ == "__main__":
    main()

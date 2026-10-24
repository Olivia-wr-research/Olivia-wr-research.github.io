import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import terrafar_select_checkpoint as selector


REPO = "owner/repository"
MAIN = ".github/workflows/terrafar-source-maintenance.yml"
CENSUS = ".github/workflows/terrafar-full-census.yml"


def run(run_id, branch="main", path=MAIN, conclusion="success", attempt=1):
    return {"id": run_id, "run_attempt": attempt, "head_branch": branch, "path": path,
            "status": "completed", "conclusion": conclusion, "event": "push", "head_sha": "a" * 40,
            "repository": {"full_name": REPO}, "head_repository": {"full_name": REPO}}


class FakeAPI:
    def __init__(self, runs):
        self.rows = runs
        self.job_rows = {}
        self.artifact_rows = {}
        self.queried_branches = []
        for row in runs:
            if row["path"] not in selector.POLICIES:
                continue
            policy = selector.POLICIES[row["path"]]
            for attempt in range(1, row["run_attempt"] + 1):
                self.job_rows[(str(row["id"]), attempt)] = [{
                    "name": policy["job"], "run_id": row["id"], "run_attempt": attempt,
                    "steps": [{"name": name, "conclusion": "success", "completed_at": f"2026-10-{row['id']:02d}T10:00:00Z"}
                              for name in policy["steps"]],
                }]
            self.artifact_rows[str(row["id"])] = [{
                "id": row["id"] + 1000,
                "name": f"{policy['artifact_prefix']}-{row['id']}-{row['run_attempt']}",
                "expired": False, "expires_at": "2099-01-01T00:00:00Z",
                "workflow_run": {"id": row["id"], "head_branch": row["head_branch"]},
            }]

    def runs(self, branch):
        self.queried_branches.append(branch)
        # Deliberately return out-of-scope rows to test local scope enforcement.
        return self.rows

    def jobs(self, run_id, attempt):
        return self.job_rows[(str(run_id), attempt)]

    def artifacts(self, run_id):
        return self.artifact_rows[str(run_id)]


class CheckpointSelectionTests(unittest.TestCase):
    def select(self, api, **kwargs):
        return selector.select_checkpoint(api, REPO, "99", kwargs.pop("branch", "main"), **kwargs)

    def test_complete_capture_from_failed_content_gate_is_selected(self):
        api = FakeAPI([run(1), run(2, conclusion="failure")])
        self.assertEqual(self.select(api)["run_id"], "2")

    def test_latest_expired_capture_fails_without_older_fallback(self):
        api = FakeAPI([run(1), run(2)])
        api.artifact_rows["2"][0]["expired"] = True
        with self.assertRaisesRegex(selector.SelectionError, "expired_no_rollback"):
            self.select(api, handoff_branch="predecessor")
        self.assertEqual(api.queried_branches, ["main"])

    def test_latest_missing_artifact_fails_without_older_fallback(self):
        api = FakeAPI([run(1), run(2)])
        api.artifact_rows["2"] = []
        with self.assertRaisesRegex(selector.SelectionError, "missing_or_ambiguous_no_rollback"):
            self.select(api)

    def test_unrelated_workflow_fork_branch_and_event_are_ignored(self):
        rows = [run(1), run(2, path=".github/workflows/ci.yml"), run(3, branch="other"), run(4), run(5)]
        rows[3]["head_repository"]["full_name"] = "fork/repository"
        rows[4]["event"] = "pull_request"
        api = FakeAPI(rows)
        self.assertEqual(self.select(api)["run_id"], "1")

    def test_self_run_is_excluded(self):
        api = FakeAPI([run(1), run(2)])
        self.assertEqual(selector.select_checkpoint(api, REPO, "2", "main")["run_id"], "1")

    def test_predecessor_requires_explicit_handoff(self):
        api = FakeAPI([run(2, branch="predecessor", path=CENSUS, conclusion="failure")])
        with self.assertRaisesRegex(selector.SelectionError, "no_complete_encrypted"):
            self.select(api)
        selected = self.select(api, handoff_branch="predecessor")
        self.assertEqual(selected["branch"], "predecessor")
        self.assertEqual(selected["restore_source"], "explicit_predecessor_handoff")
        self.assertEqual(selected["format"], "terrafar-full-census-artifact-v1")

    def test_own_branch_capture_takes_authority_after_handoff(self):
        api = FakeAPI([run(1), run(2, branch="predecessor", path=CENSUS)])
        self.assertEqual(self.select(api, handoff_branch="predecessor")["run_id"], "1")
        self.assertEqual(api.queried_branches, ["main"])

    def test_explicit_stale_restore_refused(self):
        api = FakeAPI([run(1), run(2)])
        with self.assertRaisesRegex(selector.SelectionError, "not_latest_authorized"):
            self.select(api, restore_run_id="1", restore_artifact_name=api.artifact_rows["1"][0]["name"])

    def test_failed_capture_step_is_not_a_complete_checkpoint(self):
        api = FakeAPI([run(1), run(2, conclusion="failure")])
        api.job_rows[("2", 1)][0]["steps"][1]["conclusion"] = "failure"
        self.assertEqual(self.select(api)["run_id"], "1")

    def test_earlier_attempt_is_preserved_if_later_attempt_failed_before_capture(self):
        api = FakeAPI([run(1, attempt=2), run(2)])
        api.job_rows[("1", 2)][0]["steps"][1]["conclusion"] = "failure"
        # Run 1's first capture happened after run 2; run number is not freshness.
        for step in api.job_rows[("1", 1)][0]["steps"]:
            step["completed_at"] = "2026-10-04T10:00:00Z"
        api.artifact_rows["1"][0]["name"] = "terrafar-source-maintenance-state-v3-1-1"
        selected = self.select(api)
        self.assertEqual((selected["run_id"], selected["run_attempt"]), ("1", 1))

    def test_artifact_origin_and_job_attempt_must_match(self):
        api = FakeAPI([run(1)])
        api.artifact_rows["1"][0]["workflow_run"]["id"] = 10
        with self.assertRaisesRegex(selector.SelectionError, "artifact_origin_mismatch"):
            self.select(api)
        api = FakeAPI([run(1)])
        api.job_rows[("1", 1)][0]["run_attempt"] = 2
        with self.assertRaisesRegex(selector.SelectionError, "job_origin_mismatch"):
            self.select(api)

    def test_expires_timestamp_is_checked_even_if_expired_flag_is_false(self):
        api = FakeAPI([run(1)])
        api.artifact_rows["1"][0]["expires_at"] = "2020-01-01T00:00:00Z"
        with self.assertRaisesRegex(selector.SelectionError, "expired_no_rollback"):
            self.select(api)

    def test_api_error_cannot_turn_into_empty_scope_and_handoff(self):
        class Broken(FakeAPI):
            def runs(self, branch):
                raise selector.SelectionError("github_api_http_403")
        with self.assertRaisesRegex(selector.SelectionError, "github_api_http_403"):
            self.select(Broken([]), handoff_branch="predecessor")

    def test_paginated_history_must_not_be_truncated(self):
        api = selector.GitHubAPI(REPO, None)
        api.get = lambda endpoint: {"workflow_runs": [], "total_count": 101}
        with self.assertRaisesRegex(selector.SelectionError, "history_incomplete"):
            api.runs("main")


if __name__ == "__main__":
    unittest.main()

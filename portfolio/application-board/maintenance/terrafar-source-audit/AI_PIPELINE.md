# TERRAFAR pipeline integration

## Baseline and boundaries

This implementation is stacked on PR #11 (`acc9b4c`), which includes PR #9
(`8231177`). PR #10 UI work is not included. The original dirty checkout is
preserved. Source IDs, seed mappings, website output, official opportunity data,
production workflows and owner-approval gates are unchanged. A separate bounded
transport pilot triggers only on its explicitly named feature branch.

Earlier test totals describe different trees: 130 was the older `5fed0df`
checkout plus uncommitted pipeline code; 233 was PR #9's full Python suite;
263 was PR #11's full Python suite (including 30 private persistence tests).
They are not comparable accuracy scores. Run the full suite, not a restricted
filename pattern, on this integrated branch:

```sh
python -m pip install -r portfolio/application-board/maintenance/terrafar-source-audit/private-storage/requirements.txt
python -m unittest discover -s portfolio/application-board/tests
node --test portfolio/application-board/tests/*.test.mjs
python portfolio/application-board/scripts/terrafar_source_registry.py validate
git diff --check
```

## Implemented paths

- Partial structurally parsed listings retain discovered candidates, source
  identity, content hash and incomplete scope. Unchanged lists retain pending
  reviews. A durable source cursor rotates detail work beyond the first batch.
- Detail capture reuses robots, DNS/IP validation, retry and request budgets.
  Registered individual job pages are distinguished from listing pages.
  Text truncation saves partial evidence and cannot become a terminal decision.
- Model leases cap batches at ten, attempts at three, persist receipts before
  merge, and recover interrupted merges idempotently. Quotes bind to the exact
  snapshot URL/hash. Negated portal acceptance cannot support an open result.
  Paid API execution is closed: switches or a key do not provide a scoped
  authorization or a durable call/token budget. A reviewed budget reservation
  implementation is still required before enabling that path.
- `terrafar_native_review.py` imports actual interactive session results through
  the same validator and merger. It requires a leased assignment, source/input
  fingerprint and session/task reference. This interface does not itself prove
  a model ran; the operator must retain the real execution receipt. Native
  results, provider HTTP calls and human approvals are separate counts.
- `terrafar_web_receipts.py` indexes saved authorized web-tool responses. It
  preserves line gaps and unknown transport counts; it never fabricates HTML,
  HTTP status or a complete-source check from a rendered excerpt.
- The funnel includes carried pending tasks processed during unchanged-list
  runs, including tasks outside that run's detail budget. Independent evaluation
  returns `not_evaluable` without human gold.
- Existing private Vault persistence keeps AI files in the same encrypted,
  versioned authority and rejects task/attempt/history loss. The optional private
  cycle detail stage writes immutable run-scoped paths. A separate pipeline
  implementation hash file must match before restore can continue. Any mismatch
  requires reviewed migration; do not update the hashes just to bypass it.

## Native import (private local paths supplied by operator)

Claims must retain their originating run before work starts:

```sh
python portfolio/application-board/scripts/terrafar_model_executor.py claim \
  --ledger "$PRIVATE_STATE/candidate_ledger.json" \
  --output-dir "$PRIVATE_STATE/assignments" --owner "$REVIEWER_ID" \
  --run-id "$PROGRAM_RUN_ID" --limit 10
```

The claim command requires `--run-id`; a claim without it cannot be imported.
Older malformed claims and direct-merge results must remain visible in recovery
history. Re-importing an existing result is not another model invocation.

After a real native session processes an existing claimed batch:

```sh
python portfolio/application-board/scripts/terrafar_native_review.py \
  --ledger "$PRIVATE_STATE/candidate_ledger.json" \
  --snapshots "$PRIVATE_STATE/page_snapshots" \
  --results "$PRIVATE_STATE/model_results" \
  --assignment "$PRIVATE_STATE/assignment.json" \
  --submissions "$PRIVATE_STATE/native-submissions.json" \
  --deferred "$PRIVATE_STATE/deferred.json" \
  --run-id "$PROGRAM_RUN_ID"
```

`--deferred` is an optional JSON array for assigned tasks intentionally released
before execution. A deferral record must echo the exact claim identity and give
a reason; a defer-only import uses an empty `[]` submissions file:

```json
[
  {
    "task_id": "mtask-…",
    "candidate_id": "opp-…",
    "candidate_fingerprint": "<assigned fingerprint>",
    "attempt_id": "<assigned attempt id>",
    "lease_id": "<assigned lease id>",
    "owner": "<assigned lease owner>",
    "reason": "Reviewer unavailable before execution"
  }
]
```

The combined `submissions` and `deferred` lists may contain at most ten tasks,
with no task repeated or listed in both. A deferral is accepted only while the
exact lease is live and no provider call, response, native result, or saved
result bundle exists. The reason and claim identity are retained in the private
attempt history and an idempotent event. Replaying the same deferral leaves the
prior decision unchanged; changing its reason is a conflict. Deferrals remain
claimable and do not consume retry attempts. Actual provider failures continue
to count toward the configured retry limit; they cannot be reclassified as
deferrals or reset by later claims. The separate claim sequence records every
lease, while `attempt_number` counts retry-consuming executions.

Claims also bind the candidate review-history digest. A review added after the
claim prevents a pre-execution deferral even when a legacy worker bypassed the
executor and wrote no result file. Older claims without that digest use their
review timestamps conservatively. Unknown legacy timestamps require reconciliation;
they do not establish that a task was unexecuted.

All paths must remain private and outside the public checkout. No candidate or
page evidence belongs in a commit or public Actions artifact, even encrypted.
The private runner example remains inactive. Its optional `--detail-limit 10`
adds at most 60 transport requests after the source stage; default zero keeps it
disabled. Its proposed schedule remains 02:17 UTC / 10:17 Asia/Shanghai.
No daily native agent dispatcher is implemented or enabled by this patch.

## Isolated transport pilot

`terrafar-isolated-pilot.yml` runs only on pushes affecting its wrapper or
`terrafar_isolated_pilot.py` in `codex/terrafar-stepwise-pilot-20261025`. It has
read-only permissions, no credentials, artifact/cache uploads or deployment.
Ten registered sources share 70 source HTTP slots and 30 detail HTTP slots,
including robots, redirects and retries; at most ten details are selected.
The initial real run used 36 budget slots. The current follow-up invocation is
reduced to 30 source + 20 detail slots and four details, so the two program runs
cannot exceed 86 slots in total. Web-tool internal transport counts are not
available and are reported separately. Repeating the workflow is a fresh
collection, not historical or cross-run restoration.
The data is new isolated input, not a replacement for recovered authority.
Only fixed aggregate counters reach public logs. Runner-only bodies and
candidate records are ephemeral, so this cannot demonstrate durable private
saving or supply a later model with recovered remote evidence. Authorizing a
private destination remains necessary for that complete remote path.

## Activation and unresolved gates

Before private activation, the owner must approve the exact private runner and
storage destination, access scope, retention, backup and budget. The existing
key must match the certificate; do not generate a replacement for old state.
Restore the exact historical archive and reconcile source/candidate/review
identity before creating the reviewed runtime migration. Keep the older
160-record reconstruction separate. Then validate one real private save and
restore in a second independent environment. Two same-day runs do not prove
cross-day recovery. Actual human batch decisions and release permission remain
required; no code test, model result or snapshot digest supplies approval.

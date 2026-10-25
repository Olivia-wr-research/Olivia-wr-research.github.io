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

After a real native session processes an existing claimed batch:

```sh
python portfolio/application-board/scripts/terrafar_native_review.py \
  --ledger "$PRIVATE_STATE/candidate_ledger.json" \
  --snapshots "$PRIVATE_STATE/page_snapshots" \
  --results "$PRIVATE_STATE/model_results" \
  --assignment "$PRIVATE_STATE/assignment.json" \
  --submissions "$PRIVATE_STATE/native-submissions.json" \
  --run-id "$PROGRAM_RUN_ID"
```

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

# Status and reviewed-data release

Status logic lives in `dist/opportunity.mjs` and is shared by filters, default ordering, labels, expiry checks and export. Standing programme information is not a current application round. A review/priority date or rolling recruitment statement is not a fixed deadline. Critical conflicts suppress a selected deadline and current-open recommendation.

`status: open`, a future date, and a reachable page are insufficient for current-open recommendation. The conservative current-open predicate requires reviewed page content plus a direct, job-bound positive application-portal quote, observed no more than seven calendar days ago; negative statements, future observations, closed announcements and unresolved critical conflicts exclude it. Date-only deadlines due today require local-time rechecking. A fresh observation is still only evidence at its observation time, not a guarantee of future acceptance. Missing optional salary information does not remove a record. A paid PhD remains a study opportunity.

## Existing workflow and source of truth

Use `scripts/terrafar_prepare_data_review.py` to produce a pending patch from a verified candidate review. It evaluates the real exported active catalogue, binds all static dependencies and the exact record/URL, and refuses a stale target. Legacy pending files without this binding must be regenerated, not automatically approved. Previously verified facts must not be replaced with missing/unknown values. An announcement URL is an identity; a different application URL requires the official detail-to-portal relationship.

The release helper extends this process, rather than importing a second catalogue. `dist/reviewed-updates.mjs` holds only approved, allowlisted public field deltas; it is initially empty. Stable catalogue IDs and URLs are retained, so browser favourites and profiles keep their existing keys and identities. Full candidate ledgers, evidence snapshots and owner decisions stay outside the public checkout.

## Private pending preview

```sh
python3 scripts/terrafar_release_review.py preview \
  --patch /private-review/pending.json \
  --snapshot /private-review/detail-snapshot.json \
  --output /private-review/preview-v1
python3 server.py --root /private-review/preview-v1/site \
  --port 8918 --preview-static-fetch
```

`/private-review` is a placeholder for the owner's restricted local directory, not a new service. The existing static launcher remains loopback-only, denies writes, directory access and private JSON. Its default CSP still forbids fetches. Explicit preview mode permits only the existing public pilot/source/map JSON and read-only bootstrap paths on that same loopback origin, never arbitrary external requests. No workflow, deployment or paid service is started by these commands.

Preview verifies literal field quotes and snapshot digests, creates a separate static site and a pending owner-decision request. The site title marks it as an unapproved private preview. No approval is generated. Repeating an identical preview is idempotent; changed inputs require a new review version. To carry a known portal status, additionally provide `--portal-snapshot` with the separately bound application-portal capture; a detail page or login/button alone cannot confirm acceptance. Portal observations retain their original capture time.

## Owner decision, local application and rollback

The owner reviews the exact private preview and the intended code/data diff. The assistant records a real decision only after it is actually supplied. A decision receipt binds the patch digest, preview-manifest digest, reviewer and actual review time. It is an audit record, not cryptographic identity authentication; normal PR review and branch protection remain required. Never fabricate a decision or set an owner-approval environment variable.

```sh
python3 scripts/terrafar_release_review.py apply \
  --patch /private-review/pending.json \
  --decision /private-review/owner-decision.json \
  --preview-manifest /private-review/preview-v1/preview-manifest.json \
  --journal /private-review/release-journal.json
```

This only updates the local source and hosted-copy data module. It does not commit, push, merge or deploy. A private journal is written before either file changes; interrupted application can resume only when both file hashes remain in the exact expected before/after states. Duplicate application with the same journal adds no second update. Unreviewed source changes invalidate the decision.

If the recorded real decision explicitly authorizes rollback:

```sh
python3 scripts/terrafar_release_review.py rollback \
  --decision /private-review/owner-decision.json \
  --journal /private-review/release-journal.json
```

Rollback restores exact previous bytes, supports interrupted recovery, and refuses to overwrite later changes. Keep the journal and both before/after states private. Test decisions are synthetic offline fixtures only and do not authorize real changes.

Before any actual merge/publication, review only allowlisted public deltas, run the existing Node/Python checks, verify `dist` matches `docs/apps/application-board`, preserve all IDs and source mappings, and confirm Pages' actual publishing source. After approved publication, check the public page and its source version. Publication and production verification are not implied by a preview or passing tests.

The legacy `terrafar-source-maintenance.yml` job is guarded private-only because its artifact steps contain detailed state. This prevents an approved push to the public default branch from uploading a plaintext ledger. Existing historical artifacts and schedules are not deleted or enabled by this change; private maintenance continues in the existing private runner repository.

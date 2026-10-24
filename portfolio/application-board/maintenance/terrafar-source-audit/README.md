# TERRAFAR source audit operations

This directory contains only maintenance records and source-check tooling. It does not feed candidate results into the published opportunity data.

## Fixed source union

- `registry/source_registry.json` is the additive union of the existing website catalogues, the existing `sourcePortals`, the ETH and Jobbnorge importer endpoints, relevant endpoints cited in `SOURCE_RESEARCH_06.md`, and the 133 package seeds.
- `registry/source_registry_baseline.json` and `registry/previous_trusted_source_ids.json` are frozen ID sets. Normal runs never rewrite them.
- `registry/seed_mapping.json`, `registry/occurrence_disposition.json`, and `registry/source_research_link_review.json` preserve exact mappings, exclusions, and original provenance.
- The old official-source verification fields remain in `original_metadata`; they are not treated as current evidence.

Run the set check before source work:

```sh
python3 portfolio/application-board/scripts/terrafar_source_registry.py validate
```

A reviewed source migration must update the registry and separately review the frozen baseline change. Do not rebuild the baseline as a way to make validation pass.

## Run checks locally

```sh
python3 portfolio/application-board/scripts/terrafar_source_audit.py run --live --budget 10 --concurrency 3 --retries 1 --state-dir /path/to/restored-state --require-state --require-candidate-ledger
```

`adapter_catalog.json` defines an explicit institution, opportunity type, filter, pagination rule, and scope boundary for each configured source adapter. It is an additive runtime overlay: it does not change source IDs or the 411-row registry hash. `doc-446f8d108f9611b8` keeps all-job search and Teaching-and-research results as separate endpoints; employment, admissions, scholarship, and funding scopes remain separate. A page snapshot can be complete for that page while still not proving institution-wide opportunity coverage.

The default daily plan includes every active enabled source ID. It attempts a rotating, bounded batch of ten, reserves up to one quarter of each batch for persisted failed/blocked/partial retries while keeping at least one slot for rotation, and writes explicit `not_attempted` rows for the rest of that plan. A one-source budget alternates retry and rotation slots. The registry has no priority values, so rotation follows its stable registry order. Requests remain public HTTP(S), robots-aware, address-guarded, host-paced, and retried once for transient failures.

The candidate ledger uses stable IDs derived from source ID, endpoint ID, and candidate key. It retains pending, failed, and insufficient-evidence work across runs; unchanged lists do not clear it. A content change reopens a task while preserving the prior review and candidate versions, and results are bound to the assigned content fingerprint so stale parallel reviews cannot verify changed content. Review identity and conclusion evidence are checked separately for page content, application route, and current open status; each verified field must have a claim containing its value, and a future deadline alone cannot establish current acceptance. Old terminal results are re-audited when the evidence policy version changes. Repeated identical agent results are idempotent, and file locks serialize concurrent ledger merges.

An agent handoff is exported from the durable ledger in batches of at most ten with the pinned `terrafar-source-audit` Skill hash and a structured result schema. `merge-results` validates stable task identity, assignment, duplicates, terminal evidence, and duplicate targets before saving decisions. Manual Actions imports require both `review_results_path` and the matching `review_assignment_path`; branch validation can merge the committed, assigned result batch before the next source run. GitHub Actions does not start Codex agents, so daily automatic agent execution remains unconfigured.

Each run writes a manifest with the exact source plan, registry and adapter-catalog hashes, one result per planned source ID, endpoint outcomes, logs, candidate queue, and daily report. Cross-run restore requires a successful unexpired artifact, distinct Actions run IDs, matching hashes and supported schema versions. Failure artifacts also retain the restored state and candidate ledger for recovery review; the next automatic attempt uses the latest successful artifact and unchanged rotation cursor, so the bounded source batch is retried instead of skipped. Missing, expired, corrupt, or incompatible state stops the run; it does not create an empty baseline.

## Daily GitHub Actions schedule

`.github/workflows/terrafar-source-maintenance.yml` is the read-only replacement. It has `actions: read` and `contents: read`, does not push to a state branch, and uploads only an explicit maintenance-state artifact. Its daily time is `02:17 UTC` = `10:17 Asia/Shanghai`; scheduled workflows run only after the workflow is merged to the default branch. A push to `main` with `[daily-maintenance]` in its commit message also runs the bounded full-registry maintenance task, providing a release-time default-branch check. Manual dispatch supports the frozen ten-source sample and daily full-registry plan. The one-time Round 002 bootstrap is allowed only before a version 3 state artifact exists; the validated compatibility-v1 state artifact is accepted for that initial migration. Later runs restore only versioned v3 artifacts. An explicit restore must select the latest compatible run across repository branches, preventing old state replay. Artifacts retain for 90 days; after expiry, operators must provide an independently reviewed restore artifact rather than run from an empty state.

The broader `.github/workflows/terrafar-source-audit.yml` workflow is not present in this branch or its PR #6 base. Pages deploy configuration is not changed by this workflow; it has no Pages action or publishing permission.

## Subagents

The configured roles are `endpoint_resolver`, `opportunity_verifier`, and `audit_reviewer`, with a three-agent concurrency cap and ten-item batch limit. See `.agents/skills/terrafar-source-audit/SKILL.md` for evidence rules. Interactive Codex agents are used for source/route judgement and independent review; ordinary page access and content difference detection remain in code. Agents do not edit the registry or formal site data.

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
python3 portfolio/application-board/scripts/terrafar_source_audit.py run --live --budget 100000 --concurrency 4 --retries 1 --state-dir portfolio/application-board/maintenance/terrafar-source-audit/state
```

The runner checks all enabled logical source IDs, uses public HTTP(S) only, respects `robots.txt`, limits parallel requests and host rate, retries timeouts/429/5xx once, and records every attempt. State contains parser-success snapshots for the two reused importer adapters. Other sources with successful page fetches remain `needs_endpoint` until their intended complete page/list is located and a parser is reviewed. Failures and access restrictions never mean “no update.”

First adapter observations establish a baseline and are `partial` because there is no previous comparison. Later full checks can be `checked_changed`, `checked_unchanged`, or `checked_empty`. A successful transport response alone never means an opportunity list was fully checked.

Each run writes a manifest with the exact plan and registry hash, one JSONL result per planned source ID, and a daily Markdown/JSON report. Candidate records are not written to production site files.

## Daily GitHub Actions schedule

`.github/workflows/terrafar-source-audit.yml` is configured for 10:17 Asia/Shanghai daily and manual dispatch. It commits `state.json` and that run's evidence to a dedicated `terrafar-source-state` branch behind a single-writer concurrency group. The schedule is **not active until this feature branch is merged to the repository default branch**. Repository Actions settings must allow the workflow token to write repository contents and create/update that dedicated state branch; existing branch protection must permit the state writer. No push or merge is performed by this implementation task.

## Subagents

Project agent role templates are in `.codex/agents/`; the project config caps concurrent threads at three. Tasks are limited to ten sources each. See the installed `.agents/skills/terrafar-source-audit/SKILL.md` for evidence and output requirements. This repository's GitHub Actions runner performs deterministic HTTP and adapter work only; it does not pretend to launch Codex agents. Codex agents are used in an interactive review run for endpoint location, opportunity verification, and independent audit, with outputs kept separate from the source registry.

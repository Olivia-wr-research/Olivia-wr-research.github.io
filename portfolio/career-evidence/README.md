# Career Evidence Pipeline

**Local career document → source-linked candidate events → reviewed organization IDs → inspectable candidate trajectory.**

A small offline CLI and Python library extracted from a larger scientist-mobility project. It preserves exact source text and locators instead of turning an inferred career history into a verified biography. No LLM, API account, server or network request is needed.

## Try the complete synthetic example

Python 3.11+. From this project directory:

```sh
python -m pip install .
career-evidence extract --input examples/synthetic-career.txt --person-id synthetic-person --out runs/extracted
career-evidence verify runs/extracted
python examples/review-organizations.py runs/extracted/events.json runs/reviewed-events.json
career-evidence derive --events runs/reviewed-events.json --normalized runs/extracted/normalized.json --out runs/trajectory
career-evidence verify runs/trajectory
```

This produces **5 candidate events, 5 spells and 2 candidate organization moves** from an entirely invented fixture. One move is a return; a concurrent visiting role is not counted as a primary move. `Present` remains an unknown end date. Every output remains a machine candidate, with zero gold records.

Inspect the bundled [event output](examples/expected/extracted/events.json) and [trajectory output](examples/expected/trajectory/trajectory.json) before installing anything. They were generated with the installed wheel; CI reruns the workflow and compares every output byte.

The example helper maps only three invented institutions and rejects other person IDs. It is not an organization resolver. For your own inputs, inspect the event evidence and explicitly add appropriate `organization_id` values to a copy of `events.json` before deriving a trajectory. This step is your review responsibility; the software cannot authenticate a human reviewer or prove the supplied IDs correct.

## Outputs you can inspect

| File | Contents |
|---|---|
| `normalized.json` | Locally extracted text, source digest and line/paragraph/block/page-line locators |
| `events.json` | Candidate roles, dates, role flags, exact source evidence and locators |
| `events.csv` | Spreadsheet-safe event inventory for review |
| `trajectory.json` | Candidate spells and moves, retained evidence and input hashes |
| `manifest.json` | SHA-256 hashes for checking local file consistency |

Outputs are create-only: use a fresh directory for each run. No absolute input paths are saved. The manifest is not a signature, scientific validation or proof of reviewer identity.

## Input support and limits

- Rule extraction expects English role lines such as `Research Fellow 2010 - 2014`, uppercase institution headings and `EDUCATION` / `PROFESSIONAL EXPERIENCE` sections. This is a constrained parser, not general CV understanding.
- TXT, simple HTML and DOCX can be normalized with the standard library. Text-based PDF normalization is optional: `python -m pip install '.[pdf]'`. Scanned documents, OCR, complex page layouts and multilingual extraction are not supported or benchmarked.
- Role flags and the fixed `0.75` extraction score are heuristics, not calibrated probabilities. Inspect every event.
- Only one person's evidence from one document is accepted per derivation. Organization IDs are user-supplied, not inferred from names.
- Unknown primary start dates suppress moves for that track. Same-year transitions are not ordered automatically. Source groups do not prove continuous employment, and candidate moves do not establish a verified career transition.

## What is intentionally not published

The larger local project's real-person inputs, CVs, web snapshots, publication rosters, private research protocols, historical output folders, benchmark datasets, vendor trees and environment files are excluded. Its placeholder stage commands and unfinished review interface are also excluded. This release does not claim to be that full pipeline, to automate human review, or to reproduce a private scientific study.

The original project's 127-test result does **not** describe this public edition. Run this edition's own offline tests:

```sh
python -m unittest discover -s tests -v
```

This edition has 31 offline tests. They exercise synthetic parsing, source locators, unknown dates, concurrent-role exclusion, return-move IDs, reproducibility, organization-ID requirements, output preservation and manifest tamper checks. No real-person accuracy benchmark is included.

[中文说明](README.zh-CN.md) · [Methods and public-edition changes](docs/METHOD.md) · [Privacy](SECURITY.md)

MIT licensed. Code and documentation were prepared with AI assistance. No extraction accuracy, user adoption, productivity improvement or production readiness is claimed.

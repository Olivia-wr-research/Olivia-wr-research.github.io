---
name: lit-review-orchestrate
description: Orchestrate an evidence-locked academic literature review or theoretical-framework workflow. Use for 文献综述, literature review, 理论框架, theoretical framework, theory synthesis, mechanism review, or end-to-end academic synthesis; route to the smallest relevant literature skills and use subagents for large read-heavy corpora.
---

## Path scope

This is a repository-scoped skill. Locate the workbench root containing `AGENTS.md`, `templates/` and `scripts/` (three parents above this skill folder). All `references/`, `scripts/` and project artifact paths below are relative to that root, not this skill directory. Read only the references needed for the assigned task. Do not install this folder alone as a standalone skill.

# Literature Review Orchestrator

## Purpose

Run an end-to-end or partial literature/theory workflow without collapsing search, evidence, interpretation, synthesis, and writing into one step.

## Start

1. Read root `AGENTS.md`.
2. Identify the active project under `projects/`. If none exists and the user wants a durable project, run `python3 scripts/bootstrap_project.py` with a safe slug.
3. Read `00_protocol/project_brief.md` and `00_protocol/review_protocol.md` when present.
4. Determine which gate the task actually requires; do not rerun completed gates unnecessarily.

## Routing

- discovery/query design → `$lit-search`
- inclusion/exclusion → `$lit-screen`
- paper reading/extraction → `$lit-extract-evidence`
- theory/construct analysis → `$lit-map-theory`
- causal process synthesis → `$lit-synthesize-mechanisms`
- data/method/identification review → `$lit-map-methods`
- research gap diagnosis → `$lit-diagnose-gaps`
- theoretical framework → `$lit-build-framework`
- claim/citation verification → `$lit-audit-citations`
- final academic prose → `$lit-write-review`

Use only the minimal set necessary for the user's request.

## Multi-agent orchestration

For >=20 papers, >=3 independent analytical streams, or a corpus too large for one thread, delegate bounded read-heavy tasks in parallel. Prefer project custom agents defined in `.codex/agents/`. Keep final integration in the parent thread.

Recommended sequence for a full review:

1. source_scout workers by concept/query family;
2. merge/deduplicate and screen;
3. evidence_reader workers on non-overlapping paper batches;
4. theory_analyst + mechanism_analyst + methods_analyst in parallel over the structured evidence;
5. gap diagnosis;
6. framework_architect;
7. skeptical_reviewer;
8. synthesis_editor only after audit.

## Gate discipline

Never claim a gate is complete merely because prose exists. Completion requires the corresponding artifact:

- G0: protocol
- G1: search log
- G2: screening decisions
- G3: evidence matrix
- G4: theory/mechanism/method matrices as relevant
- G5: synthesis/gap records
- G6: framework canvas
- G7: claim ledger/audit report
- G8: draft

If a source cannot be accessed, mark UNKNOWN/INACCESSIBLE rather than reconstructing content from memory.

## Finish

Run `python3 scripts/summarize_project.py <project-dir>` when useful. State completed gates, unresolved evidence gaps, and the next evidence-dependent step. Do not present an incomplete review as systematic or exhaustive.

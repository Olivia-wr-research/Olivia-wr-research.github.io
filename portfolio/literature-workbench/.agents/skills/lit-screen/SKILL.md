---
name: lit-screen
description: Screen an academic literature corpus against explicit inclusion/exclusion criteria. Use for 文献筛选, title/abstract screening, full-text screening, PRISMA-like selection, relevance filtering, inclusion decisions, or resolving borderline papers.
---

## Path scope

This is a repository-scoped skill. Locate the workbench root containing `AGENTS.md`, `templates/` and `scripts/` (three parents above this skill folder). All `references/`, `scripts/` and project artifact paths below are relative to that root, not this skill directory. Read only the references needed for the assigned task. Do not install this folder alone as a standalone skill.

# Literature Screening

## Workflow

1. Read the project review protocol and `references/screening-rules.md`.
2. Apply Stage 1 title/abstract screening, preserving UNCERTAIN cases.
3. Apply Stage 2 full-text verification when required and accessible.
4. Record one explicit reason code for each exclusion and a note when the code is insufficient.
5. Keep relevance separate from venue prestige or citation count.
6. Retain foundational or contradictory sources when they are theoretically essential even if they fall outside the dominant empirical design.
7. Deduplicate carefully; do not delete distinct versions silently.
8. Produce counts by decision and reason.

## Output files

Update `02_screening/screening_decisions.csv` and, if useful, a short `02_screening/screening_summary.md`.

Never treat inaccessible full text as evidence of irrelevance. Use UNCERTAIN or INSUFFICIENT_ACCESS where appropriate.

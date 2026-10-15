---
name: lit-diagnose-gaps
description: Diagnose defensible research gaps from an audited literature base. Use for 研究缺口, research gap, novelty, contribution positioning, unresolved debate, contradiction, boundary conditions, measurement gaps, or method gaps; reject unsupported “few studies” novelty claims.
---

## Path scope

This is a repository-scoped skill. Locate the workbench root containing `AGENTS.md`, `templates/` and `scripts/` (three parents above this skill folder). All `references/`, `scripts/` and project artifact paths below are relative to that root, not this skill directory. Read only the references needed for the assigned task. Do not install this folder alone as a standalone skill.

# Research Gap Diagnosis

## Workflow

1. Read `references/gap-taxonomy.md`.
2. Use search, evidence, theory, mechanism, and methods artifacts as available.
3. Generate candidate gaps by type: theoretical integration, mechanism, boundary condition, construct/measurement, identification/method, temporal/dynamic, contradiction/anomaly, scope/context.
4. For each candidate ask:
   - What exact unresolved problem exists?
   - What evidence demonstrates it?
   - Why does resolving it alter theory or inference?
   - What contradictory evidence weakens the gap claim?
   - What would a study need to do to close it?
5. Populate `09_synthesis/gap_matrix.csv`.
6. Rank gaps by defensibility and theoretical value, not novelty rhetoric.

## Reject

A gap is weak if it is only “not yet studied,” “few papers,” “new country,” or “new method” without a reason the omission changes theoretical expectation or inference.

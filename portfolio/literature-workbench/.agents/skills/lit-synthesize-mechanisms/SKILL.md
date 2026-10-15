---
name: lit-synthesize-mechanisms
description: Synthesize causal mechanisms across academic studies. Use for 影响机制, mechanism synthesis, mediators, causal pathways, process models, policy-to-outcome logic, or when categories/themes must be converted into an explanatory process; explicitly distinguish mechanisms from topic or policy categories.
---

## Path scope

This is a repository-scoped skill. Locate the workbench root containing `AGENTS.md`, `templates/` and `scripts/` (three parents above this skill folder). All `references/`, `scripts/` and project artifact paths below are relative to that root, not this skill directory. Read only the references needed for the assigned task. Do not install this folder alone as a standalone skill.

# Mechanism Synthesis

## Workflow

1. Read `references/theory-vs-mechanism.md`.
2. Start from paper-level mechanism claims and empirical tests in the evidence matrix.
3. Normalize overlapping labels only when their causal process is genuinely equivalent.
4. Represent each mechanism as:
   `antecedent -> intermediate state/opportunity/constraint -> decision/behavior process -> outcome`.
5. Record mediators, moderators, temporal ordering, and rival mechanisms.
6. Assign evidence status: DIRECTLY_TESTED / EXPLICITLY_ASSERTED / INDIRECTLY_SUPPORTED / ANALYST_INFERRED.
7. Populate `06_mechanisms/mechanism_matrix.csv`.
8. Compare supportive, null, and contradictory evidence.
9. Identify which mechanisms operate at different levels or stages rather than forcing them into one flat list.

## Do not

- call policy domains mechanisms;
- call independent variables mechanisms;
- infer mediation from a simple coefficient change without design support;
- present E3 synthesis as an author claim.

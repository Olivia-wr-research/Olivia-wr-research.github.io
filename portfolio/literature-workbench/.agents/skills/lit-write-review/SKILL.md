---
name: lit-write-review
description: Write or revise an academic literature review/theory section from an existing evidence base. Use for 撰写文献综述, literature review writing, theory section, synthesis section, manuscript background, or turning audited matrices into argument-driven prose; do not invent missing evidence or citations.
---

## Path scope

This is a repository-scoped skill. Locate the workbench root containing `AGENTS.md`, `templates/` and `scripts/` (three parents above this skill folder). All `references/`, `scripts/` and project artifact paths below are relative to that root, not this skill directory. Read only the references needed for the assigned task. Do not install this folder alone as a standalone skill.

# Literature Review Writing

## Preconditions

Read `references/writing-rules.md`. Prefer an audited evidence base and claim ledger. If missing, label the output provisional.

## Workflow

1. Identify the intended argument and target venue/audience.
2. Choose an organizing logic: theory, mechanism, debate, process, multilevel, historical, or methods.
3. Build a synthesis outline before prose.
4. Write paragraphs around synthesis claims, not author-by-author lists.
5. Attach only citations that support the exact claim.
6. Preserve contradictory evidence and boundary conditions.
7. Calibrate causal language to study design.
8. Keep literature-supported claims distinct from the proposed framework.
9. Maintain stable construct terminology.
10. After drafting, invoke `$lit-audit-citations` before calling the section final.

## Style

Use the user's requested language and disciplinary register. In Chinese academic prose, prefer precise conceptual transitions and avoid translated-AI filler such as repetitive “此外/值得注意的是” chains without argumentative function.

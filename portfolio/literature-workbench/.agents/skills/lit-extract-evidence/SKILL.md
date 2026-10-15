---
name: lit-extract-evidence
description: Extract structured, source-traceable evidence from academic papers. Use for 逐篇读文献, evidence matrix, paper coding, theory/method/finding extraction, source quotes/pages, or turning PDFs/articles into a literature evidence database while separating author claims from analyst interpretation.
---

## Path scope

This is a repository-scoped skill. Locate the workbench root containing `AGENTS.md`, `templates/` and `scripts/` (three parents above this skill folder). All `references/`, `scripts/` and project artifact paths below are relative to that root, not this skill directory. Read only the references needed for the assigned task. Do not install this folder alone as a standalone skill.

# Paper Evidence Extraction

## Workflow

1. Read `references/evidence-model.md` and `references/evidence-levels.md`.
2. Work only from sources actually available in the current task.
3. For each paper populate the schema in `04_evidence/evidence_matrix.csv`.
4. Capture precise source locators for decisive claims whenever possible.
5. Separate:
   - source fact/result;
   - author claim;
   - mechanism evidence;
   - agent interpretation.
6. Code E0–E4 conservatively.
7. Record null, negative, mixed, or contradictory findings.
8. Record access limitations explicitly.
9. For large corpora, delegate non-overlapping batches to `evidence_reader` subagents and merge structured records, not prose.
10. Run `python3 scripts/validate_evidence.py <evidence-matrix.csv>` after updates.

## Quality bar

A paper is not “read” for this workflow merely because its abstract or metadata was seen. Mark access status precisely and limit extraction to what that access supports.

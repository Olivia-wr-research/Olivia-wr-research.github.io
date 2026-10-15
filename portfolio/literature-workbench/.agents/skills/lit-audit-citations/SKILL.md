---
name: lit-audit-citations
description: Audit academic claims against their cited evidence. Use for 引文核查, citation audit, claim-evidence verification, hallucination checking, page/source tracing, causal-language audit, contradiction audit, or validating a literature review/theory section before submission.
---

## Path scope

This is a repository-scoped skill. Locate the workbench root containing `AGENTS.md`, `templates/` and `scripts/` (three parents above this skill folder). All `references/`, `scripts/` and project artifact paths below are relative to that root, not this skill directory. Read only the references needed for the assigned task. Do not install this folder alone as a standalone skill.

# Citation & Evidence Audit

## Workflow

1. Read `references/citation-audit.md` and `references/evidence-levels.md`.
2. Parse the draft into material claims.
3. Add or update records in `11_audit/claim_ledger.csv`.
4. For each claim verify exact support, scope, causality, attribution, locator, and contradictory evidence.
5. Reopen original sources for CRITICAL or MAJOR claims when possible.
6. Detect citation bundling where only some references support the sentence.
7. Detect E3/E4 material written as literature fact.
8. Detect construct label drift between the evidence base, framework, and prose.
9. Write `11_audit/audit_report.md` with severity-ranked findings.
10. Do not mark PASS while any CRITICAL issue remains.

## Output status

Use one of:
- PASS
- PASS_WITH_MINOR_ISSUES
- FAIL_RECOVERABLE
- FAIL_MATERIAL

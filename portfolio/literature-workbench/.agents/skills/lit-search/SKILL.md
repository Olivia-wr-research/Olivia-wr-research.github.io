---
name: lit-search
description: Design and execute reproducible academic literature searches. Use for 文献检索, systematic search, search strategy, keywords, Boolean queries, citation chasing, core-paper discovery, latest literature, or building a search log; never claim access to a database that was not actually queried.
---

## Path scope

This is a repository-scoped skill. Locate the workbench root containing `AGENTS.md`, `templates/` and `scripts/` (three parents above this skill folder). All `references/`, `scripts/` and project artifact paths below are relative to that root, not this skill directory. Read only the references needed for the assigned task. Do not install this folder alone as a standalone skill.

# Literature Search

## Inputs

Research question, scope, target literature, available databases/tools, and any seed papers.

## Workflow

1. Read `references/search-strategy.md`.
2. Decompose the question into concept families and disciplinary aliases.
3. Build precision, recall, theory/mechanism, contradiction, and citation-chasing query families.
4. Execute searches only through sources/tools actually available in the current environment.
5. Record every real search in `01_search/search_log.csv` using the exact query and access mode.
6. Normalize metadata and deduplicate by DOI first, then stable title/author/year evidence.
7. Identify seed/core papers using relevance and intellectual role, not citation count alone.
8. Use backward/forward citation chasing when available.
9. Search specifically for critiques, null results, alternative mechanisms, and newer reviews.
10. Apply a documented stopping rule.

## Output

Return:
- search concept map;
- exact query families;
- actual sources/databases used;
- candidate corpus with stable identifiers;
- gaps in access;
- saturation/stopping status.

Do not write literature-review prose during discovery unless the user explicitly asks for a provisional search summary.

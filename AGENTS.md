# Repository instructions

## TERRAFAR source maintenance

- Treat source IDs in `portfolio/application-board/maintenance/terrafar-source-audit/registry/` as persistent identifiers. Never regenerate or remove a source to make a run appear complete.
- Read and follow `.agents/skills/terrafar-source-audit/SKILL.md` before source reconciliation or opportunity verification.
- Keep checks, candidate data, and evidence under `portfolio/application-board/maintenance/terrafar-source-audit/`; do not write candidate opportunities into the formal site data without a separate reviewed process.
- Preserve raw URLs and provenance. Canonicalization may remove `utm_*` tracking parameters only; do not merge by domain or infer deadlines, funding, qualifications, or status.
- Do not edit published website appearance. `portfolio/application-board/dist/` is the website source output; `docs/apps/application-board/` is the published copy. For this maintenance task, neither directory should change.
- Source registry changes require a reviewed migration and the set-preservation checks in `scripts/terrafar_source_registry.py validate`.
- Daily checks must emit one terminal status per planned source and keep failed, blocked, and unattempted sources distinct from no-change results.
- Native subagent work is limited to three concurrent agents and batches of at most ten sources. Agents write only to isolated task outputs; the root process owns merge and release decisions.

# Multi-Agent Literature Workflow

## Principle

Use subagents for bounded read-heavy work; keep protocol decisions, integration, and final writing in the parent thread.

## Recommended split

### Corpus discovery
Spawn source scouts by concept family, discipline, geography, or time period. Merge and deduplicate before screening.

### Evidence extraction
Split included papers into non-overlapping batches. Every evidence reader uses the same extraction schema.

### Orthogonal analyses
Run theory, mechanism, and methods analysts on the same audited evidence matrix. Because they answer different questions, their outputs can be parallel.

### Adversarial review
After synthesis/framework drafting, run skeptical reviewer independently. Do not reveal a desired conclusion in the reviewer prompt.

## Merge rule

Never concatenate agent prose blindly. Merge at the level of structured records, claim IDs, theory IDs, mechanism IDs, and contradiction notes.

## Context hygiene

The parent thread should retain:

- review protocol;
- inclusion decisions;
- schema definitions;
- high-level synthesis decisions;
- unresolved contradictions;
- framework versions;
- audit findings.

It should not retain every raw reading note when those are already stored in project files.
